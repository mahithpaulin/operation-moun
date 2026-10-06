"""Byte-level tokenizer: no training, no pretrained vocab. Bytes are tokens."""
PAD, BOS, EOS = 256, 257, 258
VOCAB = 512  # 256 bytes + specials + headroom


def encode(s: str) -> list:
    return [BOS] + list(s.encode("utf-8", errors="replace")) + [EOS]


def decode(ids) -> str:
    bs = bytes([i for i in ids if i < 256])
    return bs.decode("utf-8", errors="replace")


def pack(seqs, pad_to=None, pad_id=PAD):
    n = pad_to or max(len(s) for s in seqs)
    import torch
    return torch.tensor([s[:n] + [pad_id] * max(0, n - len(s)) for s in seqs])
