//! Native wgpu renderer for elemental-ui material packs.
//!
//! The shader is `shaders/elemental_surface.wgsl`, the same file the web
//! runtime loads, so a native render and a WebGPU render of the same pack and
//! parameters should match to within rounding. [`SurfaceRenderer`] works with
//! any target format; [`render_offscreen`] is the headless path used by the
//! `elemental-render` CLI and the parity tests.
//!
//! GPL-3.0-only.

use bytemuck::{Pod, Zeroable};
use elemental_pack::{Pack, Rgba8};

pub const SHADER_SOURCE: &str = include_str!("../../../shaders/elemental_surface.wgsl");

/// Mirrors `struct Params` in the WGSL (std140-compatible, 64 bytes).
#[repr(C)]
#[derive(Debug, Clone, Copy, PartialEq, Pod, Zeroable)]
pub struct SurfaceParams {
    pub resolution: [f32; 2],
    pub tile_px: f32,
    pub relief: f32,
    /// xyz toward the light (x right, y up, z toward viewer); w intensity.
    pub light: [f32; 4],
    /// rgb light color; a ambient fraction.
    pub light_color: [f32; 4],
    /// xy offset in tiles; z exposure; w unused.
    pub view: [f32; 4],
}

impl SurfaceParams {
    /// The reference look used by the CLI, web demo and parity tests.
    pub fn reference(width: u32, height: u32) -> Self {
        Self {
            resolution: [width as f32, height as f32],
            tile_px: 256.0,
            relief: 1.0,
            light: [-0.45, 0.55, 0.70, 3.2],
            light_color: [1.0, 0.97, 0.92, 0.22],
            view: [0.0, 0.0, 1.0, 0.0],
        }
    }
}

#[derive(Debug)]
pub enum RenderError {
    Pack(elemental_pack::Error),
    NoAdapter(String),
    Device(String),
    Readback(String),
}

impl std::fmt::Display for RenderError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RenderError::Pack(e) => write!(f, "pack: {e}"),
            RenderError::NoAdapter(e) => write!(f, "no GPU adapter: {e}"),
            RenderError::Device(e) => write!(f, "device: {e}"),
            RenderError::Readback(e) => write!(f, "readback: {e}"),
        }
    }
}

impl std::error::Error for RenderError {}

impl From<elemental_pack::Error> for RenderError {
    fn from(e: elemental_pack::Error) -> Self {
        RenderError::Pack(e)
    }
}

/// GPU resources for one material, drawable into any target of `format`.
pub struct SurfaceRenderer {
    pipeline: wgpu::RenderPipeline,
    uniforms: wgpu::Buffer,
    bind_group: wgpu::BindGroup,
}

fn upload(device: &wgpu::Device, queue: &wgpu::Queue, label: &str, image: &Rgba8, format: wgpu::TextureFormat) -> wgpu::TextureView {
    let size = wgpu::Extent3d { width: image.width, height: image.height, depth_or_array_layers: 1 };
    let texture = device.create_texture(&wgpu::TextureDescriptor {
        label: Some(label),
        size,
        mip_level_count: 1,
        sample_count: 1,
        dimension: wgpu::TextureDimension::D2,
        format,
        usage: wgpu::TextureUsages::TEXTURE_BINDING | wgpu::TextureUsages::COPY_DST,
        view_formats: &[],
    });
    queue.write_texture(
        wgpu::TexelCopyTextureInfo { texture: &texture, mip_level: 0, origin: wgpu::Origin3d::ZERO, aspect: wgpu::TextureAspect::All },
        &image.pixels,
        wgpu::TexelCopyBufferLayout { offset: 0, bytes_per_row: Some(image.width * 4), rows_per_image: Some(image.height) },
        size,
    );
    texture.create_view(&wgpu::TextureViewDescriptor::default())
}

impl SurfaceRenderer {
    pub fn new(device: &wgpu::Device, queue: &wgpu::Queue, pack: &Pack, format: wgpu::TextureFormat) -> Result<Self, RenderError> {
        let basecolor = upload(device, queue, "basecolor", &pack.load_rgba8("basecolor")?, wgpu::TextureFormat::Rgba8UnormSrgb);
        let normal = upload(device, queue, "normal", &pack.load_rgba8("normal")?, wgpu::TextureFormat::Rgba8Unorm);
        let roughness = upload(device, queue, "roughness", &pack.load_rgba8("roughness")?, wgpu::TextureFormat::Rgba8Unorm);
        let sampler = device.create_sampler(&wgpu::SamplerDescriptor {
            label: Some("material"),
            address_mode_u: wgpu::AddressMode::Repeat,
            address_mode_v: wgpu::AddressMode::Repeat,
            mag_filter: wgpu::FilterMode::Linear,
            min_filter: wgpu::FilterMode::Linear,
            ..Default::default()
        });
        let uniforms = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("params"),
            size: std::mem::size_of::<SurfaceParams>() as u64,
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });
        let module = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("elemental_surface.wgsl"),
            source: wgpu::ShaderSource::Wgsl(SHADER_SOURCE.into()),
        });
        let pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("elemental surface"),
            layout: None,
            vertex: wgpu::VertexState { module: &module, entry_point: Some("vs_main"), compilation_options: Default::default(), buffers: &[] },
            fragment: Some(wgpu::FragmentState {
                module: &module,
                entry_point: Some("fs_main"),
                compilation_options: Default::default(),
                targets: &[Some(wgpu::ColorTargetState { format, blend: None, write_mask: wgpu::ColorWrites::ALL })],
            }),
            primitive: wgpu::PrimitiveState::default(),
            depth_stencil: None,
            multisample: wgpu::MultisampleState::default(),
            multiview_mask: None,
            cache: None,
        });
        let bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("material"),
            layout: &pipeline.get_bind_group_layout(0),
            entries: &[
                wgpu::BindGroupEntry { binding: 0, resource: uniforms.as_entire_binding() },
                wgpu::BindGroupEntry { binding: 1, resource: wgpu::BindingResource::Sampler(&sampler) },
                wgpu::BindGroupEntry { binding: 2, resource: wgpu::BindingResource::TextureView(&basecolor) },
                wgpu::BindGroupEntry { binding: 3, resource: wgpu::BindingResource::TextureView(&normal) },
                wgpu::BindGroupEntry { binding: 4, resource: wgpu::BindingResource::TextureView(&roughness) },
            ],
        });
        Ok(Self { pipeline, uniforms, bind_group })
    }

    /// Record one full-target draw. The caller submits the encoder.
    pub fn draw(&self, queue: &wgpu::Queue, encoder: &mut wgpu::CommandEncoder, target: &wgpu::TextureView, params: &SurfaceParams) {
        queue.write_buffer(&self.uniforms, 0, bytemuck::bytes_of(params));
        let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
            label: Some("elemental surface"),
            color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                view: target,
                depth_slice: None,
                resolve_target: None,
                ops: wgpu::Operations { load: wgpu::LoadOp::Clear(wgpu::Color::BLACK), store: wgpu::StoreOp::Store },
            })],
            depth_stencil_attachment: None,
            timestamp_writes: None,
            occlusion_query_set: None,
            multiview_mask: None,
        });
        pass.set_pipeline(&self.pipeline);
        pass.set_bind_group(0, &self.bind_group, &[]);
        pass.draw(0..3, 0..1);
    }
}

/// Headless GPU context.
pub struct Gpu {
    pub adapter_info: wgpu::AdapterInfo,
    pub device: wgpu::Device,
    pub queue: wgpu::Queue,
}

impl Gpu {
    pub fn headless() -> Result<Self, RenderError> {
        pollster::block_on(async {
            let instance = wgpu::Instance::new(wgpu::InstanceDescriptor::new_without_display_handle_from_env());
            let adapter = instance
                .request_adapter(&wgpu::RequestAdapterOptions {
                    power_preference: wgpu::PowerPreference::HighPerformance,
                    force_fallback_adapter: false,
                    compatible_surface: None,
                    ..Default::default()
                })
                .await
                .map_err(|e| RenderError::NoAdapter(e.to_string()))?;
            let adapter_info = adapter.get_info();
            let (device, queue) = adapter
                .request_device(&wgpu::DeviceDescriptor { label: Some("elemental"), ..Default::default() })
                .await
                .map_err(|e| RenderError::Device(e.to_string()))?;
            Ok(Self { adapter_info, device, queue })
        })
    }
}

/// Render a pack into an RGBA8 buffer (sRGB-encoded by the shader).
pub fn render_offscreen(gpu: &Gpu, pack: &Pack, params: &SurfaceParams, width: u32, height: u32) -> Result<Vec<u8>, RenderError> {
    let format = wgpu::TextureFormat::Rgba8Unorm;
    let renderer = SurfaceRenderer::new(&gpu.device, &gpu.queue, pack, format)?;
    let size = wgpu::Extent3d { width, height, depth_or_array_layers: 1 };
    let target = gpu.device.create_texture(&wgpu::TextureDescriptor {
        label: Some("offscreen"),
        size,
        mip_level_count: 1,
        sample_count: 1,
        dimension: wgpu::TextureDimension::D2,
        format,
        usage: wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::COPY_SRC,
        view_formats: &[],
    });
    let view = target.create_view(&wgpu::TextureViewDescriptor::default());
    let padded = (width * 4).div_ceil(wgpu::COPY_BYTES_PER_ROW_ALIGNMENT) * wgpu::COPY_BYTES_PER_ROW_ALIGNMENT;
    let readback = gpu.device.create_buffer(&wgpu::BufferDescriptor {
        label: Some("readback"),
        size: u64::from(padded) * u64::from(height),
        usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
        mapped_at_creation: false,
    });
    let mut encoder = gpu.device.create_command_encoder(&wgpu::CommandEncoderDescriptor { label: Some("offscreen") });
    renderer.draw(&gpu.queue, &mut encoder, &view, params);
    encoder.copy_texture_to_buffer(
        wgpu::TexelCopyTextureInfo { texture: &target, mip_level: 0, origin: wgpu::Origin3d::ZERO, aspect: wgpu::TextureAspect::All },
        wgpu::TexelCopyBufferInfo {
            buffer: &readback,
            layout: wgpu::TexelCopyBufferLayout { offset: 0, bytes_per_row: Some(padded), rows_per_image: Some(height) },
        },
        size,
    );
    gpu.queue.submit([encoder.finish()]);
    let slice = readback.slice(..);
    let (tx, rx) = std::sync::mpsc::channel();
    slice.map_async(wgpu::MapMode::Read, move |r| {
        let _ = tx.send(r);
    });
    gpu.device
        .poll(wgpu::PollType::wait_indefinitely())
        .map_err(|e| RenderError::Readback(e.to_string()))?;
    rx.recv()
        .map_err(|e| RenderError::Readback(e.to_string()))?
        .map_err(|e| RenderError::Readback(e.to_string()))?;
    let mapped = slice.get_mapped_range().map_err(|e| RenderError::Readback(e.to_string()))?;
    let mut pixels = Vec::with_capacity((width * height * 4) as usize);
    for row in mapped.chunks_exact(padded as usize) {
        pixels.extend_from_slice(&row[..(width * 4) as usize]);
    }
    drop(mapped);
    readback.unmap();
    Ok(pixels)
}

/// Encode RGBA8 pixels as PNG.
pub fn encode_png(pixels: &[u8], width: u32, height: u32) -> Vec<u8> {
    let mut out = Vec::new();
    {
        let mut encoder = png::Encoder::new(&mut out, width, height);
        encoder.set_color(png::ColorType::Rgba);
        encoder.set_depth(png::BitDepth::Eight);
        let mut writer = encoder.write_header().expect("png header");
        writer.write_image_data(pixels).expect("png data");
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::Path;

    #[test]
    fn params_match_wgsl_layout() {
        assert_eq!(std::mem::size_of::<SurfaceParams>(), 64);
    }

    #[test]
    fn shader_validates_with_naga() {
        let module = naga::front::wgsl::parse_str(SHADER_SOURCE).expect("WGSL parses");
        naga::valid::Validator::new(naga::valid::ValidationFlags::all(), naga::valid::Capabilities::empty())
            .validate(&module)
            .expect("WGSL validates");
    }

    #[test]
    fn renders_basalt_offscreen_when_a_gpu_exists() {
        let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../packs/geo.basalt.vesicular.v1");
        if !dir.join("pack.json").is_file() {
            eprintln!("skipped: run `python3 tools/elemental.py pack` first");
            return;
        }
        let gpu = match Gpu::headless() {
            Ok(gpu) => gpu,
            Err(e) => {
                eprintln!("skipped: {e}");
                return;
            }
        };
        let pack = Pack::open(&dir).unwrap();
        let pixels = render_offscreen(&gpu, &pack, &SurfaceParams::reference(256, 256), 256, 256).unwrap();
        assert_eq!(pixels.len(), 256 * 256 * 4);
        let lum: Vec<f64> = pixels.chunks_exact(4).map(|p| f64::from(p[0]) + f64::from(p[1]) + f64::from(p[2])).collect();
        let mean = lum.iter().sum::<f64>() / lum.len() as f64;
        let var = lum.iter().map(|l| (l - mean).powi(2)).sum::<f64>() / lum.len() as f64;
        assert!(mean > 10.0 && mean < 700.0, "mean {mean}");
        assert!(var > 50.0, "render is flat (variance {var})");
    }
}
