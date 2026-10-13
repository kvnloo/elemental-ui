//! Read and verify `elemental-pack/1` material packs.
//!
//! A pack is a directory written by `tools/elemental.py pack`: a `pack.json`
//! manifest plus GPU-repeatable maps. This crate is the Rust side of that
//! contract; `packages/web/src/pack.ts` is the TypeScript side.
//!
//! GPL-3.0-only.

use std::collections::BTreeMap;
use std::fmt;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use serde::Deserialize;
use sha2::{Digest, Sha256};

pub const SCHEMA: &str = "elemental-pack/1";
pub const MAP_NAMES: [&str; 4] = ["basecolor", "normal", "roughness", "height"];

#[derive(Debug, Clone, Deserialize)]
pub struct Manifest {
    pub schema: String,
    pub id: String,
    pub display_name: String,
    pub family: String,
    pub class: Option<String>,
    pub kind: String,
    pub license: String,
    pub status: String,
    pub physical_tile_mm: f64,
    pub height_mm: f64,
    pub normal_convention: String,
    pub tiling: String,
    pub maps: BTreeMap<String, MapEntry>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct MapEntry {
    pub file: String,
    pub mime: String,
    pub width: u32,
    pub height: u32,
    pub bit_depth: u8,
    pub color_space: String,
    pub sha256: String,
    pub bytes: u64,
    #[serde(default)]
    pub variants: Vec<Variant>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Variant {
    pub file: String,
    pub mime: String,
    pub sha256: String,
    pub bytes: u64,
}

#[derive(Debug)]
pub enum Error {
    Io(PathBuf, io::Error),
    Json(PathBuf, serde_json::Error),
    Png(PathBuf, png::DecodingError),
    Invalid(String),
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Io(path, e) => write!(f, "{}: {e}", path.display()),
            Error::Json(path, e) => write!(f, "{}: {e}", path.display()),
            Error::Png(path, e) => write!(f, "{}: {e}", path.display()),
            Error::Invalid(message) => f.write_str(message),
        }
    }
}

impl std::error::Error for Error {}

/// RGBA8 pixels of one map, expanded from the stored PNG layout.
#[derive(Debug, Clone)]
pub struct Rgba8 {
    pub width: u32,
    pub height: u32,
    pub pixels: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct Pack {
    pub dir: PathBuf,
    pub manifest: Manifest,
}

impl Pack {
    /// Open `dir/pack.json` and check its schema and required maps.
    pub fn open(dir: impl AsRef<Path>) -> Result<Self, Error> {
        let dir = dir.as_ref().to_path_buf();
        let path = dir.join("pack.json");
        let text = fs::read_to_string(&path).map_err(|e| Error::Io(path.clone(), e))?;
        let manifest: Manifest = serde_json::from_str(&text).map_err(|e| Error::Json(path.clone(), e))?;
        if manifest.schema != SCHEMA {
            return Err(Error::Invalid(format!("{}: schema {:?} is not {SCHEMA}", path.display(), manifest.schema)));
        }
        for name in MAP_NAMES {
            if !manifest.maps.contains_key(name) {
                return Err(Error::Invalid(format!("{}: missing map {name}", path.display())));
            }
        }
        Ok(Self { dir, manifest })
    }

    pub fn map(&self, name: &str) -> Result<&MapEntry, Error> {
        self.manifest
            .maps
            .get(name)
            .ok_or_else(|| Error::Invalid(format!("{}: no map {name}", self.manifest.id)))
    }

    /// Hash every map and variant against the manifest.
    pub fn verify(&self) -> Result<(), Error> {
        for entry in self.manifest.maps.values() {
            let files = std::iter::once((&entry.file, &entry.sha256))
                .chain(entry.variants.iter().map(|v| (&v.file, &v.sha256)));
            for (file, expected) in files {
                let path = self.dir.join(file);
                let data = fs::read(&path).map_err(|e| Error::Io(path.clone(), e))?;
                let actual = hex(&Sha256::digest(&data));
                if &actual != expected {
                    return Err(Error::Invalid(format!("{}: sha256 {actual} != {expected}", path.display())));
                }
            }
        }
        Ok(())
    }

    /// Decode an 8-bit map (basecolor, normal, roughness) to RGBA8.
    pub fn load_rgba8(&self, name: &str) -> Result<Rgba8, Error> {
        let entry = self.map(name)?;
        let path = self.dir.join(&entry.file);
        let file = fs::File::open(&path).map_err(|e| Error::Io(path.clone(), e))?;
        let mut reader = png::Decoder::new(io::BufReader::new(file))
            .read_info()
            .map_err(|e| Error::Png(path.clone(), e))?;
        let mut buf = vec![0; reader.output_buffer_size().unwrap_or(0)];
        let info = reader.next_frame(&mut buf).map_err(|e| Error::Png(path.clone(), e))?;
        if info.bit_depth != png::BitDepth::Eight {
            return Err(Error::Invalid(format!("{}: expected 8-bit map", path.display())));
        }
        let data = &buf[..info.buffer_size()];
        let pixels = match info.color_type {
            png::ColorType::Rgba => data.to_vec(),
            png::ColorType::Rgb => data.chunks_exact(3).flat_map(|p| [p[0], p[1], p[2], 255]).collect(),
            png::ColorType::Grayscale => data.iter().flat_map(|&g| [g, g, g, 255]).collect(),
            other => return Err(Error::Invalid(format!("{}: unsupported color type {other:?}", path.display()))),
        };
        Ok(Rgba8 { width: info.width, height: info.height, pixels })
    }
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn packs_dir() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../packs")
    }

    #[test]
    fn reads_and_verifies_built_packs() {
        let index = packs_dir().join("index.json");
        if !index.is_file() {
            eprintln!("skipped: run `python3 tools/elemental.py pack` first");
            return;
        }
        let pack = Pack::open(packs_dir().join("geo.basalt.vesicular.v1")).expect("open");
        pack.verify().expect("hashes match");
        let base = pack.load_rgba8("basecolor").expect("decode");
        assert_eq!(base.pixels.len(), (base.width * base.height * 4) as usize);
        assert_eq!(pack.map("basecolor").unwrap().color_space, "srgb");
        assert_eq!(pack.manifest.normal_convention, "opengl-y-up");
    }
}
