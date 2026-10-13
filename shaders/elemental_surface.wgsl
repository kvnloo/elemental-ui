// elemental-ui surface shader. GPL-3.0-only.
//
// The single lighting source for every runtime:
//   native: wgpu (crates/elemental-render) loads this file directly
//   web:    WebGPU loads this file directly; WebGL2 uses GLSL ES 3.00 that naga
//           generates from this file (packages/web/scripts/build-glsl.mjs)
//
// It relights a tiling material pack (sRGB base color, OpenGL +Y tangent
// normal, linear roughness) under one directional light. Output is
// sRGB-encoded by hand so an rgba8unorm/bgra8unorm target gives the same bytes
// on every backend.

struct Params {
    // Target size in physical pixels.
    resolution: vec2<f32>,
    // On-screen size of one material tile, in physical pixels.
    tile_px: f32,
    // Multiplier on the tangent-space normal's xy (1.0 = authored relief).
    relief: f32,
    // xyz: direction toward the light (x right, y up, z toward the viewer).
    // w: light intensity.
    light: vec4<f32>,
    // rgb: light color. a: ambient fraction of base color.
    light_color: vec4<f32>,
    // xy: texture offset in tiles. z: exposure. w: unused.
    view: vec4<f32>,
};

@group(0) @binding(0) var<uniform> params: Params;
@group(0) @binding(1) var material_sampler: sampler;
@group(0) @binding(2) var basecolor_map: texture_2d<f32>;
@group(0) @binding(3) var normal_map: texture_2d<f32>;
@group(0) @binding(4) var roughness_map: texture_2d<f32>;

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

const PI: f32 = 3.14159265;

@vertex
fn vs_main(@builtin(vertex_index) index: u32) -> VertexOut {
    // One triangle that covers the viewport; uv (0,0) is the top-left pixel.
    let x = f32((index << 1u) & 2u);
    let y = f32(index & 2u);
    var out: VertexOut;
    out.position = vec4<f32>(x * 2.0 - 1.0, 1.0 - y * 2.0, 0.0, 1.0);
    out.uv = vec2<f32>(x, y);
    return out;
}

fn linear_to_srgb(c: vec3<f32>) -> vec3<f32> {
    let lo = c * 12.92;
    let hi = 1.055 * pow(c, vec3<f32>(1.0 / 2.4)) - 0.055;
    return select(hi, lo, c <= vec3<f32>(0.0031308));
}

@fragment
fn fs_main(in: VertexOut) -> @location(0) vec4<f32> {
    let uv = in.uv * params.resolution / params.tile_px + params.view.xy;

    // basecolor_map is an sRGB texture, so sampling returns linear color.
    let base = textureSample(basecolor_map, material_sampler, uv).rgb;
    let encoded = textureSample(normal_map, material_sampler, uv).xyz * 2.0 - 1.0;
    let roughness = clamp(textureSample(roughness_map, material_sampler, uv).r, 0.045, 1.0);

    let n = normalize(vec3<f32>(encoded.xy * params.relief, encoded.z));
    let l = normalize(params.light.xyz);
    let v = vec3<f32>(0.0, 0.0, 1.0);
    let h = normalize(l + v);
    let n_dot_l = max(dot(n, l), 0.0);
    let n_dot_h = max(dot(n, h), 0.0);
    let n_dot_v = max(dot(n, v), 1e-4);

    // GGX distribution, Smith-Schlick visibility, Schlick Fresnel (dielectric).
    let a = roughness * roughness;
    let a2 = a * a;
    let d_denom = n_dot_h * n_dot_h * (a2 - 1.0) + 1.0;
    let distribution = a2 / (PI * d_denom * d_denom);
    let k = a * 0.5;
    let visibility = 1.0 / ((n_dot_l * (1.0 - k) + k) * (n_dot_v * (1.0 - k) + k) * 4.0);
    let fresnel = 0.04 + 0.96 * pow(1.0 - max(dot(h, v), 0.0), 5.0);
    let specular = distribution * visibility * fresnel;

    let radiance = params.light_color.rgb * params.light.w;
    let direct = (base * (1.0 - fresnel) / PI + vec3<f32>(specular)) * radiance * n_dot_l;
    let ambient = base * params.light_color.a;
    let exposed = (direct + ambient) * params.view.z;
    // Reinhard keeps highlights from clipping without a separate tone-map pass.
    let mapped = exposed / (vec3<f32>(1.0) + exposed);
    return vec4<f32>(linear_to_srgb(mapped), 1.0);
}
