# 🌟 Docker Configuration

The structure of this repo is being defined not by sensible thought, but by God himself. That is to say, I have no idea what it'll look like, I'm waiting for divine inspiration

## 📁 Structure

I can imagine that this repo will eventually have an output of one deployed "product" (I'll use this to brush up on my devops skills). In that sense, each "service" that is actually
a part of the final product (and therefore has a deployment process) will have a folder in here with a `Dockerfile`, `requirements`, etc. Maybe simple services (like `postgres`, `redis` etc)
don't need their own folder, and will just be entirely defined in the compose stack. The `docker-compose.yml` should stay in this folder, and `up.sh` in the repo root should "just work"
to launch the product, at least in dev, maybe even in "prod"

