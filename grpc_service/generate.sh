rm -rf customerpb
mkdir -p customerpb
touch customerpb/__init__.py

python -m grpc_tools.protoc \
  -I proto \
  --python_out=customerpb \
  --grpc_python_out=customerpb \
  proto/customer.proto