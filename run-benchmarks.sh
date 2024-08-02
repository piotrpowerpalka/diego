# Create setup for hello benchmark

cd benchmark/hello
docker build -t spade_hello .
docker compose up -d
cd ../..
