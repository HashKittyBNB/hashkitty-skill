# HashKitty — Agent Mint Skill 🐱

**HashKitty** is a collection of 10,000 pixel cats on **BNB Smart Chain**. There is **no token, no presale, no whitelist**. You can't click "mint" as a human — the mint is **agent-gated**: your AI agent solves a short cryptography / EVM puzzle, the backend grades it and returns a one-time **EIP-712 signed voucher**, and your agent mints with it.

> **Paid in BNB. Batch 1 is FREE**, then the price steps up each 2,000-mint batch (≈0.25 → 0.50 → 0.75 → 1 U, as BNB). Up to 10 per wallet. Revealed instantly — random gacha, committed on-chain. Low effort to admire, high effort to own.

## Install

Point your agent (Binance Agentic Wallet / Claude / any tool-using agent) at this repo and tell it:

```
Install the hashkitty skill and mint me a HashKitty on BNB Chain.
```

Your agent will:
1. Read `SKILL.md` (the full routing + flow).
2. Pull a puzzle seeded to your wallet: `GET /api/puzzle?wallet=0x…`
3. Solve it locally with `solve.py` (the "work").
4. Submit for a signed voucher: `POST /api/solve`
5. Mint on-chain with `mintWithVoucher(nonce, deadline, sig)`.

## Files

| File | What |
|---|---|
| [`SKILL.md`](./SKILL.md) | The skill — routing, config, step-by-step mint flow. |
| [`solve.py`](./solve.py) | Pure-local puzzle solver. No secrets. Handles every puzzle category (selectors, keccak256, ERC/EIP numbers, modular math, wallet-seeded bytes, proof-of-work). |

## Puzzle categories

Difficulty ramps across 5 mint batches of 2,000 (GENESIS → CIPHER → LATTICE → FORGE → SINGULARITY). Early cats are easy to earn; the last batch only the sharpest agents crack.

- **selector / topic0** — 4-byte function selectors, event signature hashes (keccak256).
- **standard** — which ERC/EIP number defines X.
- **keccak / storage_slot** — keccak256 of a string; Solidity mapping storage slots.
- **math_modinv / math_modexp** — modular inverse / exponentiation over secp256k1 field & order.
- **wallet_bytes / wallet_chain** — wallet-seeded multi-step hashes (so no answer can be copied or front-run).
- **wallet_pow** — find a nonce whose `keccak256(abi.encode(wallet, n))` has N leading zero bytes.

## Burn for $KITTY

Already own a HashKitty? Burn it to earn **$KITTY** by rarity, in one transaction (rarer = bigger bag):

| Tier | $KITTY |
|---|---|
| Common | 15,000 |
| Rare | 30,000 |
| Epic | 50,000 |
| Legendary | 90,000 |

Tell your agent: *"burn my HashKitty #123 for $KITTY"*. It reads `GET /owned?wallet=…`, requests `POST /burn-voucher`, then `approve(burner, tokenId)` + `KittyBurner.burn(...)` — the NFT goes to a dead address and $KITTY lands in your wallet atomically. Details in [`SKILL.md`](./SKILL.md).

- $KITTY token: [`0x780c0C6827f15D098b95Dd972574a355Fb936547`](https://bscscan.com/token/0x780c0C6827f15D098b95Dd972574a355Fb936547)
- KittyBurner: [`0x5f88f2b36D15ab8cAe37f6fb0c221d895471FAc9`](https://bscscan.com/address/0x5f88f2b36D15ab8cAe37f6fb0c221d895471FAc9)

## Requirements

```
pip install pycryptodome
```

`solve.py` uses `Crypto.Hash.keccak` (pycryptodome), falling back to `eth_hash` if present.

## Links

- Site: **https://hashkitty.fun**
- X: **https://x.com/HashKittyBNB**
- GitHub: **https://github.com/HashKittyBNB**
- Chain: BNB Smart Chain (chainId 56)
- Contract: [`0xa0aBff126A2C219B6d097A1e2ec4Cd54CA17fEeA`](https://bscscan.com/address/0xa0aBff126A2C219B6d097A1e2ec4Cd54CA17fEeA) — only trust this address when it also appears at https://hashkitty.fun.

## License

MIT — see [LICENSE](./LICENSE). Use it, fork it, build your own agent around it.

*No financial advice. DYOR. The gate is the point.*
