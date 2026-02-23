# Cast Advanced Usage

Advanced cast commands for blockchain interaction, decoding, and analysis.

## Transaction Decoding

### Decode Transaction

```bash
# Decode transaction by hash
cast decode-tx 0x1234... --rpc-url mainnet

# Output includes:
# - from, to, value
# - function selector
# - decoded calldata
# - gas used
```

### 4byte Signature Lookup

```bash
# Get function name from selector
cast 4byte 0xa9059cbb
# transfer(address,uint256)

# Get selector from signature
cast sig "transfer(address,uint256)"
# 0xa9059cbb

# Decode calldata with known selector
cast 4byte-decode 0xa9059cbb000000000000000000000000...
```

### Decode Calldata

```bash
# Decode with ABI
cast calldata-decode "transfer(address,uint256)" 0xa9059cbb...

# Output:
# 0x1234...  [address]
# 1000000    [uint256]
```

## ABI Encoding/Decoding

### Encode Function Call

```bash
# Encode calldata
cast calldata "transfer(address,uint256)" 0x1234... 1000000
# 0xa9059cbb000000000000000000000000...

# Encode with complex types
cast calldata "swap((address,uint256,bytes))" "(0x1234...,100,0x)"
```

### Encode Arguments

```bash
# ABI encode
cast abi-encode "constructor(string,uint256)" "Token" 1000000

# ABI encode packed
cast abi-encode --packed "test(string)" "hello"
```

### Decode ABI Data

```bash
# Decode return data
cast abi-decode "balanceOf(address)(uint256)" 0x00000000...
# 1000000

# Decode with multiple returns
cast abi-decode "getReserves()(uint112,uint112,uint32)" 0x...
```

## Wallet Management

### Create Wallet

```bash
# Generate new wallet
cast wallet new

# Generate with mnemonic
cast wallet new-mnemonic

# Derive from mnemonic
cast wallet derive-private-key "word1 word2 ... word12"
```

### Wallet Info

```bash
# Get address from private key
cast wallet address --private-key 0x...

# Get address from mnemonic
cast wallet address --mnemonic "word1 word2..."

# Sign message
cast wallet sign "message" --private-key 0x...
```

### Keystore

```bash
# Import to keystore
cast wallet import my-wallet --private-key 0x...

# List keystores
cast wallet list

# Use keystore
cast send ... --account my-wallet
```

## Contract Interaction

### Read Functions

```bash
# Call view function
cast call $CONTRACT "balanceOf(address)" $USER --rpc-url mainnet

# With block number
cast call $CONTRACT "balanceOf(address)" $USER --block 18000000

# Decode result
cast call $CONTRACT "decimals()" | cast to-dec
```

### Write Functions

```bash
# Send transaction
cast send $CONTRACT "transfer(address,uint256)" $TO $AMOUNT \
  --private-key $KEY \
  --rpc-url mainnet

# With value
cast send $CONTRACT "deposit()" --value 1ether --private-key $KEY

# Estimate gas
cast estimate $CONTRACT "transfer(address,uint256)" $TO $AMOUNT
```

## Storage Inspection

```bash
# Read storage slot
cast storage $CONTRACT 0 --rpc-url mainnet

# Read multiple slots
for i in {0..10}; do
  echo "Slot $i: $(cast storage $CONTRACT $i)"
done

# Find storage slot for mapping
cast index address $KEY 0  # mapping at slot 0
```

## Block & Transaction Info

```bash
# Get block
cast block latest --rpc-url mainnet
cast block 18000000 --field timestamp

# Get transaction
cast tx 0x1234... --rpc-url mainnet

# Get receipt
cast receipt 0x1234... --rpc-url mainnet

# Get logs
cast logs --from-block 18000000 --to-block 18000100 \
  --address $CONTRACT \
  --topic0 0xddf252ad...  # Transfer event
```

## Type Conversions

```bash
# Hex to decimal
cast to-dec 0x64
# 100

# Decimal to hex
cast to-hex 100
# 0x64

# Wei conversions
cast to-wei 1 ether
# 1000000000000000000

cast from-wei 1000000000000000000
# 1.000000000000000000

# ASCII/bytes conversions
cast to-ascii 0x68656c6c6f
# hello

cast from-utf8 "hello"
# 0x68656c6c6f
```

## Address Utilities

```bash
# Checksum address
cast to-checksum-address 0x1234...

# Compute CREATE address
cast compute-address $DEPLOYER --nonce 5

# Compute CREATE2 address
cast create2 --starts-with 0x1234 --init-code 0x...
```

## ENS

```bash
# Resolve ENS name
cast resolve-name vitalik.eth --rpc-url mainnet

# Lookup address
cast lookup-address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

## Gas

```bash
# Get gas price
cast gas-price --rpc-url mainnet

# Get base fee
cast base-fee --rpc-url mainnet

# Estimate gas
cast estimate $CONTRACT "transfer(address,uint256)" $TO $AMOUNT
```

## Batch Operations

```bash
# Multiple calls with bash
for addr in $ADDR1 $ADDR2 $ADDR3; do
  echo "$addr: $(cast call $TOKEN 'balanceOf(address)' $addr | cast to-dec)"
done

# Using multicall3
cast call 0xcA11bde05977b3631167028862bE2a173976CA11 \
  "aggregate((address,bytes)[])" \
  "[($TOKEN,$(cast calldata 'balanceOf(address)' $ADDR1)),...]"
```
