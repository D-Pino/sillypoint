# 🎮 SillyPoint

A personal playground repo for learning and experimenting with different technologies.

## 🚀 Projects

<table>
  <tr>
    <td><h3><b>batpad</b> 📝</h3></td>
    <td>A Django-based web application for maybe learning some web dev (barebones, not in progress)</td>
  </tr>
  <tr>
    <td><h3><b>fineleg</b> 🦀</h3></td>
    <td>A project to learn Rust. Currently toying around with polars and pointclouds, and using rerun for viz</td>
  </tr>
  <tr>
    <td><h3><b>firstslip</b> 🔬</h3></td>
    <td>To play around with python and/or ML models</td>
  </tr>
  <tr>
    <td><h3><b>cowcorner</b> 🐄</h3></td>
    <td>Small python project to use sqlalchemy and alembic to manage a database. Might also use this to practise some ETLs and data ingestion</td>
  </tr>
  <tr>
    <td><h3><b>thirdman</b> 🤖</h3></td>
    <td>Robotics simulation exploration using Isaac Sim for learning robotics concepts and simulation</td>
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
