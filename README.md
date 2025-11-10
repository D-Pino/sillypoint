# 🎮 SillyPoint

A personal playground repo for learning and experimenting with different technologies.

## 🚀 Projects

<table>
  <tr>
    <td><h3><b>batpad</b> 📝</h3></td>
    <td>Explore some web dev with Django and React</td>
  </tr>
  <tr>
    <td><h3><b>fineleg</b> 🦀</h3></td>
    <td>A project to learn Rust. Currently toying around with polars and pointclouds, and using rerun for viz</td>
  </tr>
  <tr>
    <td><h3><b>firstslip</b> 🔬</h3></td>
    <td>CV and ML</td>
  </tr>
  <tr>
    <td><h3><b>cowcorner</b> 🐄</h3></td>
    <td>Short experiment in data ingestion to practise some data modeling / pipeline work</td>
  </tr>
  <tr>
    <td><h3><b>thirdman</b> 🤖</h3></td>
    <td>Trying to generate robotics sim environments with natural language</td>
  </tr>
</table>

## 🛠️ Setup dev environment (reminders to self) (ubuntu 24) (this isn't separated by project)

### Docker
Follow the [official Docker installation guide](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)

After installation, set up perms to make life easier:
```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

### Python Tools
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Install pre-commit:
  ```bash
  uv tool install pre-commit

  # Setup pre-commit hooks
  pre-commit install
  ```

### Rust Tools
- Install [Rust](https://www.rust-lang.org/tools/install)
- Install rerun (the viewer, not the SDK) - [Official docs](https://rerun.io/docs/getting-started/installing-viewer#installing-the-viewer)
  ```bash
  cargo install cargo-binstall
  cargo binstall rerun-cli
  ```
