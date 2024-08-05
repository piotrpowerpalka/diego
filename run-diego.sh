# Create setup for hello benchmark
#
cd diego/hello
docker build -t spade_hello .
docker compose up -d
cd ../..
