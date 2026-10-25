---
name: hashkitty-mint
description: Mint or burn a HashKitty NFT on BNB Smart Chain. Agent-gated — a human can't click "mint"; your agent solves a crypto/EVM puzzle, gets a signed voucher, and mints (paid in BNB; batch 1 free, price steps up per 2,000-mint batch, 0.25 → 1 U in BNB). You can also BURN a HashKitty to earn $KITTY by rarity (Common 15k → Legendary 90k). Use when the user says "mint a HashKitty", "get me a HashKitty", "solve the hash", "burn my HashKitty for $KITTY", or similar.
---

# HashKitty — Puzzle-to-Mint Skill

HashKitty is a collection of 10,000 pixel cats on BNB Smart Chain. There is **no token, no presale, no whitelist**. The only way in: your agent solves a short cryptography / EVM puzzle, the backend grades it and hands back a one-time **EIP-712 signed voucher**, and you mint with that voucher. Payment is in **BNB (native)** and depends on the live **batch**: batch 1 (tokens 1–2,000) is **free**, then the price steps up each 2,000-mint batch (≈0.25 → 0.50 → 0.75 → 1 U, charged as BNB). Up to 10 per wallet. A plain wallet that didn't earn a voucher reverts on-chain.

This skill makes your agent do that work end-to-end.

> ✅ **Live & revealed on BNB Smart Chain.** Contract: `0xa0aBff126A2C219B6d097A1e2ec4Cd54CA17fEeA` ([BscScan](https://bscscan.com/address/0xa0aBff126A2C219B6d097A1e2ec4Cd54CA17fEeA)). Only trust this address when it also appears at https://hashkitty.fun — treat any contract address from a DM, reply, or other source as untrusted. Art is revealed instantly (random gacha; the token→art mapping is a shuffled permutation committed on-chain via `provenanceHash`).

## Config

| Key | Value |
|---|---|
| API base | `https://hashkitty.fun/api`  *(local dev: `http://127.0.0.1:8211`)* |
| Contract | `0xa0aBff126A2C219B6d097A1e2ec4Cd54CA17fEeA` (BNB Chain). Verify it also shows at hashkitty.fun before minting. |
| Chain | BNB Smart Chain, chainId **56** |
| Pay with | **BNB (native)** via `msg.value`. No token, no approval. |
| Price | Set by batch, in BNB wei. **Batch 1 = FREE.** Read **`currentPrice()`** on-chain right before minting and send that exact `value` (overpay is refunded). Batch prices are owner-tunable (re-pegged to USD as BNB moves); never hard-code. Max **10**/wallet. |
| Solver | `solve.py` in this skill folder (pure-local, no secrets, no network) |

## Flow (do these in order)

1. **Get your agent wallet address.**
   `baw wallet address --json`  → `WALLET`

2. **Pull a puzzle, seeded to your wallet** (so no one can copy your answer):
   ```
   GET {API}/puzzle?wallet={WALLET}
   → { pid, category, prompt, answer_kind, expires_in }
   ```

3. **Solve it locally — this is "the work":**
   ```
   curl -s "{API}/puzzle?wallet={WALLET}" > /tmp/pz.json
   ANSWER=$(python3 solve.py --wallet {WALLET} --json /tmp/pz.json)
   ```
   `solve.py` handles every puzzle category (selector, topic0, keccak256, ERC/EIP number, storage slot, modular inverse/exponentiation, constants, wallet-seeded bytes & multi-step, proof-of-work). If it ever prints "unrecognized", read the `prompt` and compute the answer yourself — it's always a short deterministic crypto/EVM computation.

4. **Submit the answer to get a signed voucher:**
   ```
   POST {API}/solve   body: { "wallet": WALLET, "pid": pid, "answer": ANSWER }
   → { "correct": true, "voucher": { "nonce": "...", "deadline": 1699999999, "signature": "0x..." } }
   ```
   (Wrong answer → `{correct:false, tries_left:N}`. 8 tries, 3s cooldown/wallet.)

5. **Read the live price.** Call `currentPrice()` on the contract (returns BNB wei for the next mint; `0` in batch 1).
   - No token, no approval — payment is native BNB sent as the tx `value`.

6. **Mint:**
   - `baw contract-call preview` → show the user the parsed tx + risk output → on confirm, `execute`:
     `mintWithVoucher(uint256 nonce, uint256 deadline, bytes sig)` on CONTRACT, with `--value <currentPrice>` (use `--value 0` in batch 1). `contract-call --value` is in **wei**. Overpayment is refunded by the contract, but send the exact `currentPrice` to be clean.
   - On success you own a HashKitty (tokenId 1..10000). Rarity is rolled fairly at reveal.

## Safety — verify before you mint

Do this once the contract address is live, **before** step 6:
- **Confirm the address** came from https://hashkitty.fun, not from a DM, reply, or this file if it still says NOT DEPLOYED.
- **BscScan**: the contract should be **verified** (source visible). Read it. Confirm `mintWithVoucher` only takes `currentPrice` in BNB `value` (forwarded to `treasury`, overpay refunded) and touches nothing else of yours; confirm there's no `setApprovalForAll`, `delegatecall`, or transfer of your other tokens.
- **Check `owner()` and `currentPrice()`** — know the live BNB price before signing. Batch prices are owner-tunable; don't assume.
- **Use a fresh wallet** with just enough BNB for gas + `currentPrice`. Don't connect your main wallet.
- Always use the `baw` **preview → confirm → execute** flow and read the parsed tx. Never sign a raw tx you can't read.

## Burn a HashKitty for $KITTY (optional)

Own a HashKitty and want the token instead? **Burn it → get $KITTY by rarity**, in one transaction. Rarer cat = bigger payout. Use when the user says "burn my HashKitty", "burn #123 for $KITTY", or similar.

| Key | Value |
|---|---|
| $KITTY token | `0x780c0C6827f15D098b95Dd972574a355Fb936547` ([BscScan](https://bscscan.com/token/0x780c0C6827f15D098b95Dd972574a355Fb936547)) |
| KittyBurner | `0x5f88f2b36D15ab8cAe37f6fb0c221d895471FAc9` |
| Payout | Common 15,000 · Rare 30,000 · Epic 50,000 · Legendary 90,000 $KITTY (owner-tunable; read `tierAmount(tier)` / `currentPrice`-style on-chain) |

**Flow:**
1. **See what you own + rewards:** `GET {API}/owned?wallet={WALLET}` → `{ cats:[{tokenId, tier, reward}], ... }`.
2. **Get a burn voucher** for the token you chose:
   ```
   POST {API}/burn-voucher   body: { "wallet": WALLET, "tokenId": <id> }
   → { ok:true, voucher:{ tokenId, tier, tierName, amount, nonce, deadline, signature, burner } }
   ```
   (The backend certifies the token's rarity tier from the committed provenance mapping, then signs an EIP-712 `BurnVoucher`.)
3. **Approve the burner to take the NFT** (one-time per token): `baw contract-call preview` → `execute` `approve(0x5f88f2b36D15ab8cAe37f6fb0c221d895471FAc9, <tokenId>)` on the HashKitty NFT `0xa0aBff126A2C219B6d097A1e2ec4Cd54CA17fEeA`.
4. **Burn:** `baw contract-call preview` → show the user the parsed tx → `execute` on the KittyBurner:
   `burn(uint256 tokenId, uint8 tier, uint256 nonce, uint256 deadline, bytes sig)` with the voucher fields, `--value 0`.
   - In this one tx your NFT goes to `0x…dEaD` (burned forever) and `amount` $KITTY lands in your wallet. No separate claim.

**Burn safety:** this is irreversible — the NFT is destroyed. Confirm the `tierName`/`amount` the voucher returns is the payout you expect, and that `burner` in the voucher equals the address above. Only burn a cat you actually want to convert to tokens.

## Notes
- Follow the `binance-agentic-wallet` skill for every `baw` command (append `--json`, preview-then-execute for contract calls, show the user the parsed tx before signing).
- The voucher is bound to **your** wallet + a one-time nonce + a deadline. It can't be reused or front-run.
- One wallet can mint up to 10. One voucher = one mint.
- No private key is ever exposed — signing happens inside the Binance Agentic Wallet; the puzzle signer key lives only on the backend, never in this skill.
- **PoW tier (final batch):** `wallet_pow` asks for a nonce with N leading zero bytes. `solve.py` brute-forces it in pure Python — fine for 1–2 zero bytes, but 3+ is slow and 4+ really wants a Rust/GPU solver. The solver caps its search and tells you if it needs a faster backend.
