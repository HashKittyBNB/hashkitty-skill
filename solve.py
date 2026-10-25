#!/usr/bin/env python3
"""
HashKitty agent-side puzzle solver.

Takes a puzzle prompt (from GET /puzzle) and computes the answer LOCALLY.
No server secret involved — this is exactly "the work" an agent does to earn a cat.

Usage:
    python3 solve.py --wallet 0xYOURWALLET --prompt "What is the 4-byte function selector of `transfer(address,uint256)`? (0x-prefixed)"
    # or pipe the whole /puzzle JSON:
    curl -s "$API/puzzle?wallet=0xYOURWALLET" | python3 solve.py --wallet 0xYOURWALLET --json -

Prints the answer string on stdout (nothing else), exit 0 on success.
"""
import sys, os, re, json, argparse

try:
    from Crypto.Hash import keccak as _k
    def keccak256(b: bytes) -> bytes:
        h = _k.new(digest_bits=256); h.update(b); return h.digest()
except Exception:
    from eth_hash.auto import keccak as keccak256  # fallback

SECP_P = 2**256 - 2**32 - 977
SECP_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def selector(sig: str) -> str:
    return "0x" + keccak256(sig.encode())[:4].hex()

def pad32(it) -> bytes:
    if isinstance(it, str) and it.startswith("0x"):
        return int(it, 16).to_bytes(32, "big")
    return int(it).to_bytes(32, "big")

def abi_encode(*items) -> bytes:
    return b"".join(pad32(x) for x in items)

# EIP/ERC knowledge the agent is expected to know (easy tier)
STANDARDS = [
    ("the standard interface for fungible tokens", 20),
    ("the standard interface for non-fungible tokens (NFTs)", 721),
    ("the multi-token standard (fungible + non-fungible in one contract)", 1155),
    ("token-bound accounts (a smart-contract account for every NFT)", 6551),
    ("the tokenized-vault standard", 4626),
    ("the NFT royalty-info standard", 2981),
    ("standard interface detection (supportsInterface)", 165),
    ("the fee-market change that introduced the base fee", 1559),
    ("the standard proxy storage slots (implementation / admin / beacon)", 1967),
    ("typed structured data hashing and signing", 712),
    ("the CREATE2 opcode", 1014),
    ("the Diamond / multi-facet proxy standard", 2535),
    ("simple replay attack protection (chainId in the signed tx)", 155),
    ("the signed data standard", 191),
    ("account abstraction using an alt mempool and EntryPoint", 4337),
    ("standard signature validation for contracts (isValidSignature)", 1271),
    ("the permit extension (approvals via signatures) for ERC-20", 2612),
]

def solve(prompt: str, wallet: str = "") -> str:
    low = prompt.lower()

    # 1. chainId of BNB Smart Chain
    if "chainid" in low and "bnb" in low:
        return "56"

    # wallet_chain multi-step (contains "selector of" too — handle BEFORE plain selector)
    if "Multi-step" in prompt or "XOR 56" in prompt:
        sig = re.search(r"selector of `([^`]+)`", prompt).group(1)
        rnd = int(re.search(r"uint256\((\d+)\)\)\)", prompt).group(1))
        w = re.search(r"yourWallet = (0x[0-9a-fA-F]{40})", prompt).group(1)
        x = int(selector(sig), 16) ^ 56
        return "0x" + keccak256(abi_encode(x, int(w, 16), rnd)).hex()

    # 2. function selector
    m = re.search(r"selector of `([^`]+)`", prompt)
    if m:
        return selector(m.group(1))

    # 3. topic0 / event signature hash (full 32 bytes)
    m = re.search(r"topic0 .*?of `([^`]+)`", prompt)
    if m:
        return "0x" + keccak256(m.group(1).encode()).hex()

    # 4. keccak256 of an ASCII string
    m = re.search(r'ASCII string "([^"]+)"', prompt)
    if m:
        return "0x" + keccak256(m.group(1).encode()).hex()

    # 5. which ERC/EIP number
    m = re.search(r"Which ERC/EIP number defines (.+?)\? \(", prompt)
    if m:
        desc = m.group(1).strip()
        cands = [(d, num) for d, num in STANDARDS if d in desc or desc in d]
        if cands:
            # pick the most-specific (longest) matching description
            return str(max(cands, key=lambda c: len(c[0]))[1])

    # 6. storage slot: keccak256(abi.encode(key, slot))
    m = re.search(r"storage slot (\d+).*?key (0x[0-9a-fA-F]{40})", prompt, re.S)
    if m:
        slot = int(m.group(1)); key = m.group(2)
        return "0x" + keccak256(abi_encode(key, slot)).hex()

    # 7. modular inverse mod n
    m = re.search(r"modular inverse of (\d+) modulo n", prompt)
    if m:
        return str(pow(int(m.group(1)), -1, SECP_N))

    # 8. modular exponentiation mod p:  base^exp mod p
    m = re.search(r"Compute (\d+)\^(\d+) mod p", prompt)
    if m:
        return str(pow(int(m.group(1)), int(m.group(2)), SECP_P))

    # 9. constants
    if "field prime p" in low:
        return str(SECP_P)
    if "curve order n" in low:
        return str(SECP_N)
    if "eip-1967 implementation slot" in low:
        return "0x" + (int.from_bytes(keccak256(b"eip1967.proxy.implementation"), "big") - 1).to_bytes(32, "big").hex()

    # 11. wallet-seeded bytes: x = keccak256(abi.encodePacked(yourWallet, uint256(R))), bytes 12..31
    m = re.search(r"abi\.encodePacked\(yourWallet, uint256\((\d+)\)\).*?yourWallet = (0x[0-9a-fA-F]{40})", prompt, re.S)
    if m:
        rnd = int(m.group(1)); w = m.group(2)
        x = keccak256(bytes.fromhex(w[2:]) + rnd.to_bytes(32, "big"))
        return "0x" + x[12:32].hex()

    # 12. proof-of-work: find nonce n s.t. keccak256(abi.encode(wallet, n)) has D leading zero bytes
    m = re.search(r"begins with (\d+) zero byte", prompt)
    if m:
        D = int(m.group(1))
        w = int(re.search(r"yourWallet = (0x[0-9a-fA-F]{40})", prompt).group(1), 16)
        wb = w.to_bytes(32, "big"); zero = b"\x00" * D
        cap = int(os.environ.get("HK_POW_CAP", str(1 << min(32, 8 * D + 4))))  # ~16x the expected work
        for n in range(cap):
            if keccak256(wb + n.to_bytes(32, "big"))[:D] == zero:
                return str(n)
        raise SystemExit(
            f"solve.py: proof-of-work with {D} leading zero bytes not found in {cap:,} tries "
            f"(pure-Python is slow past 2 bytes). Use a Rust/GPU keccak solver for this tier, "
            f"or raise the cap with HK_POW_CAP. Target: keccak256(abi.encode(wallet, n)) starts with {'00'*D}.")

    raise SystemExit("solve.py: unrecognized puzzle category — prompt:\n" + prompt)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wallet", default="")
    ap.add_argument("--prompt", default="")
    ap.add_argument("--json", default="", help="path to /puzzle JSON, or '-' for stdin")
    a = ap.parse_args()
    prompt = a.prompt
    if a.json:
        raw = sys.stdin.read() if a.json == "-" else open(a.json).read()
        prompt = json.loads(raw)["prompt"]
    if not prompt:
        raise SystemExit("need --prompt or --json")
    print(solve(prompt, a.wallet))

if __name__ == "__main__":
    main()
