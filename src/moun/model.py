"""Micro-decoder: vanilla decoder-only Transformer, random init."""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class RMSNorm(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.w = nn.Parameter(torch.ones(d))

    def forward(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + 1e-6) * self.w


def _rope(x, pos):
    d = x.shape[-1]
    inv = 1.0 / (10000 ** (torch.arange(0, d, 2, device=x.device).float() / d))
    ang = pos.unsqueeze(-1) * inv
    c, s = ang.cos(), ang.sin()
    x1, x2 = x[..., ::2], x[..., 1::2]
    return torch.stack([x1 * c - x2 * s, x1 * s + x2 * c], -1).flatten(-2)


class Block(nn.Module):
    def __init__(self, d, heads):
        super().__init__()
        self.n1, self.n2 = RMSNorm(d), RMSNorm(d)
        self.heads = heads
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.proj = nn.Linear(d, d, bias=False)
        self.fc1 = nn.Linear(d, 4 * d, bias=False)
        self.fc2 = nn.Linear(4 * d, d, bias=False)

    def forward(self, x):
        B, T, D = x.shape
        h = self.n1(x)
        q, k, v = self.qkv(h).chunk(3, -1)
        hd = D // self.heads
        q = q.view(B, T, self.heads, hd).transpose(1, 2)
        k = k.view(B, T, self.heads, hd).transpose(1, 2)
        v = v.view(B, T, self.heads, hd).transpose(1, 2)
        pos = torch.arange(T, device=x.device)
        q, k = _rope(q, pos), _rope(k, pos)
        mask = torch.ones(T, T, device=x.device).tril().bool()
        att = (q @ k.transpose(-2, -1) / math.sqrt(hd)).masked_fill(~mask, float("-inf"))
        y = (F.softmax(att, -1) @ v).transpose(1, 2).reshape(B, T, D)
        x = x + self.proj(y)
        return x + self.fc2(F.silu(self.fc1(self.n2(x))))


class MicroDecoder(nn.Module):
    def __init__(self, layers=2, d=64, heads=2, vocab=512, ctx=1024):
        super().__init__()
        self.tok = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList([Block(d, heads) for _ in range(layers)])
        self.norm = RMSNorm(d)
        self.head = nn.Linear(d, vocab, bias=False)
        self.ctx = ctx

    def forward(self, ids):
        x = self.tok(ids[:, -self.ctx:])
        for b in self.blocks:
            x = b(x)
        return self.head(self.norm(x))

    @torch.no_grad()
    def generate(self, prompt_ids, n_new=128, temp=0.8):
        import torch
        ids = torch.tensor([prompt_ids])
        for _ in range(n_new):
            nxt = self(ids[:, -self.ctx:])[:, -1] / max(temp, 1e-3)
            p = F.softmax(nxt, -1)
            ids = torch.cat([ids, torch.multinomial(p, 1)], 1)
            if ids[0, -1].item() == 258:  # EOS
                break
        return ids[0].tolist()


def count(m):
    return sum(p.numel() for p in m.parameters())
