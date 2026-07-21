import torch

if torch.cuda.is_available():
    print(f"CUDA可用: {torch.cuda.is_available()}")
    print(f"GPU数量: {torch.cuda.device_count()}")
    print(f"GPU名称: {torch.cuda.get_device_name(0)}")
    props = torch.cuda.get_device_properties(0)
    print(f"显存: {props.total_memory / 1024**3:.2f}GB")
    print(f"算力: {props.major}.{props.minor}")
else:
    print("CUDA不可用")
    print(f"PyTorch版本: {torch.__version__}")
