<a id="readme-top"></a>

<div align="center">
  <a href="https://github.com/aditsuru-git/ChromaScale">
    <img src="./assets/logo.png" alt="Logo" width="100" height="100">
  </a>
  <h3 align="center">ChromaScale</h3>
  <p align="center">
    A zero-effort, AI-powered image upscaler for Ubuntu.
    <br />
    <br />
    <a href="https://github.com/aditsuru-git/ChromaScale/issues/new?template=bug_report.yml">Report a Bug</a>
    ·
    <a href="https://github.com/aditsuru-git/ChromaScale/issues/new?template=feature_request.yml">Request a Feature</a>
  </p>
</div>

<div align="center">

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]
[![Release][release-shield]][release-url]

</div>

## About The Project

<div align="center">
  <img src="./assets/demo.gif" alt="ChromaScale Demo" width="100%" style="max-width: 800px;">
</div>

ChromaScale is an automated image upscaling service for Ubuntu that runs quietly in the background. Simply drop your low-resolution images into a target folder, and ChromaScale uses a powerful AI model to enhance them and save to the configured output directory — no manual intervention required.

**Core Features:**

- **Fully Automated:** Runs as a background service, starts on boot, and automatically restarts on crash.
- **High-Quality Upscaling:** Uses the Real-ESRGAN model to deliver 4x upscaling while handling noise and compression artifacts.
- **Queue-Based Processing:** Handles multiple images arriving simultaneously without missing any.
- **Configurable:** Input/output folders and “replace-file” mode can be set with a simple CLI tool.
- **GPU Accelerated:** Automatically uses your NVIDIA GPU if available; falls back to CPU otherwise.

### Built With

[![Python-badge][Python-badge]][Python-url]
[![PyTorch-badge][PyTorch-badge]][PyTorch-url]

## Getting Started

Follow these steps to get ChromaScale running on your Ubuntu system.

### Prerequisites

- Ubuntu with Python 3.10+
- `uv` package manager
- Optional: NVIDIA GPU for faster processing

Install `uv`:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation

1. Clone the repository:

```sh
git clone https://github.com/aditsuru-git/ChromaScale.git
cd ChromaScale
```

2. Run the setup script:

```sh
./setup.sh
```

This will:

- Create a safe virtual environment
- Install dependencies
- Download the Real-ESRGAN model
- Configure the background service
- Install the global CLI command `image-upscaler`

The service will start automatically after setup.

## Usage

ChromaScale runs automatically in the background. Manage it with the CLI:

**Commands:**

- Check service status:

```sh
image-upscaler status
```

- Enable or disable service:

```sh
image-upscaler enable
image-upscaler disable
```

- Check GPU/CPU usage:

```sh
image-upscaler check-gpu
```

- Configure input/output folders or enable replace-file mode:

```sh
image-upscaler set input=/path/to/input output=/path/to/output replace=True
```

> **Note:** When `replace=True`, input and output are the same, and files will be overwritten after upscaling.

### Default Behavior

- Input folder: configurable via settings (`settings.ini`)
- Output folder: configurable via settings (`settings.ini`)
- Replace-file: optional, defaults to `False`

New images dropped into the input folder are automatically queued and upscaled.

## Roadmap

- [x] Core background service with Real-ESRGAN
- [x] Queue-based image processing
- [x] Command-line interface for service management
- [ ] Support for additional upscaling models (e.g., anime)
- [ ] Optional GUI for configuration and monitoring

See open issues for a full list of proposed features.

## Contributing

Contributions are welcome! Please read our **[Contribution Guide](CONTRIBUTING.md)** for details on how to submit pull requests and follow the code of conduct.

## License

Distributed under the MIT License. See `LICENSE` for details.

> [!IMPORTANT]
> This app uses the Real-ESRGAN model (BSD 3-Clause License, Copyright (c) 2021, Xintao Wang).
> Redistribution and use of the model are subject to the BSD 3-Clause terms.

## Acknowledgments

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) for the AI upscaling model.
- [Watchdog](https://pypi.org/project/watchdog/) for robust folder monitoring.
- [Astral](https://astral.sh/) for `uv` package management.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
<h1></h1>

<div align="center">
  <img src="https://github.com/aditsuru-git/readme-template/blob/main/assets/footer-team.png?raw=true" alt="Footer Banner" width="100%" style="max-width: 1200px;">
</div>

<!-- MARKDOWN LINKS & IMAGES -->

[contributors-shield]: https://img.shields.io/github/contributors/aditsuru-git/ChromaScale
[contributors-url]: https://github.com/aditsuru-git/ChromaScale/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/aditsuru-git/ChromaScale
[forks-url]: https://github.com/aditsuru-git/ChromaScale/network/members
[stars-shield]: https://img.shields.io/github/stars/aditsuru-git/ChromaScale
[stars-url]: https://github.com/aditsuru-git/ChromaScale/stargazers
[issues-shield]: https://img.shields.io/github/issues/aditsuru-git/ChromaScale
[issues-url]: https://github.com/aditsuru-git/ChromaScale/issues
[license-shield]: https://img.shields.io/github/license/aditsuru-git/ChromaScale
[license-url]: https://github.com/aditsuru-git/ChromaScale/blob/main/LICENSE
[release-shield]: https://img.shields.io/github/v/release/aditsuru-git/ChromaScale?include_prereleases
[release-url]: https://github.com/aditsuru-git/ChromaScale/releases
[Python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[PyTorch-badge]: https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white
[PyTorch-url]: https://pytorch.org/
