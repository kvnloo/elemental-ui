//! `elemental-render`: render a material pack headlessly to PNG.
//!
//!     elemental-render PACK_DIR OUT.png [WIDTH HEIGHT]
//!
//! GPL-3.0-only.

use std::process::ExitCode;

use elemental_pack::Pack;
use elemental_render::{encode_png, render_offscreen, Gpu, SurfaceParams};

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.len() != 2 && args.len() != 4 {
        eprintln!("usage: elemental-render PACK_DIR OUT.png [WIDTH HEIGHT]");
        return ExitCode::from(2);
    }
    let (width, height) = if args.len() == 4 {
        match (args[2].parse(), args[3].parse()) {
            (Ok(w), Ok(h)) => (w, h),
            _ => {
                eprintln!("WIDTH and HEIGHT must be integers");
                return ExitCode::from(2);
            }
        }
    } else {
        (1024, 640)
    };
    let result = (|| -> Result<String, Box<dyn std::error::Error>> {
        let pack = Pack::open(&args[0])?;
        pack.verify()?;
        let gpu = Gpu::headless()?;
        let started = std::time::Instant::now();
        let pixels = render_offscreen(&gpu, &pack, &SurfaceParams::reference(width, height), width, height)?;
        let elapsed = started.elapsed();
        std::fs::write(&args[1], encode_png(&pixels, width, height))?;
        Ok(format!(
            "{} -> {} ({width}x{height}) on {} [{:?}] in {:.1} ms",
            pack.manifest.id,
            args[1],
            gpu.adapter_info.name,
            gpu.adapter_info.backend,
            elapsed.as_secs_f64() * 1000.0
        ))
    })();
    match result {
        Ok(line) => {
            println!("{line}");
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("elemental-render: {e}");
            ExitCode::FAILURE
        }
    }
}
