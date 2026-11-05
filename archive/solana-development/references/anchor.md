# Anchor Framework Reference

This reference covers Anchor-specific features and patterns. For general Solana concepts (accounts, PDAs, CPIs, etc.), see the other reference files in this directory.

## Table of Contents

- [Installation and Setup](#installation-and-setup)
- [Anchor Macros](#anchor-macros)
- [Program Structure](#program-structure)
- [Account Validation Constraints](#account-validation-constraints)
- [IDL (Interface Description Language)](#idl-interface-description-language)
- [TypeScript Client](#typescript-client)
- [Rust Client](#rust-client)
- [Anchor CLI Commands](#anchor-cli-commands)
- [Token Integration (anchor-spl)](#token-integration-anchor-spl)
- [Testing with Anchor](#testing-with-anchor)
- [Anchor Features](#anchor-features)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)

---

## Installation and Setup

### Quick Install (Mac/Linux)

```bash
# Install all dependencies (Rust, Solana CLI, Anchor)
curl --proto '=https' --tlsv1.2 -sSfL https://solana-install.solana.workers.dev | bash
```

### Install Anchor with AVM

Anchor Version Manager (avm) manages multiple Anchor CLI versions:

```bash
# Install AVM
cargo install --git https://github.com/coral-xyz/anchor avm --force

# Install latest Anchor
avm install latest
avm use latest

# Install specific version
avm install 0.32.1
avm use 0.32.1

# Install from commit hash
avm install 0.30.1-cfe82aa682138f7c6c58bf7a78f48f7d63e9e466
avm use 0.30.1-cfe82aa
```

### Verify Installation

```bash
anchor --version  # Should output: anchor-cli 0.32.1
solana --version  # Recommended: solana-cli 2.3.0+
rustc --version   # Required: 1.89.0+ for IDL builds
```

### Solana Playground (No Install)

Develop in browser at https://beta.solpg.io/

---

## Anchor Macros

### Core Macros Overview

1. **`declare_id!`** - Declares the program's on-chain address
2. **`#[program]`** - Defines the program module containing instructions
3. **`#[derive(Accounts)]`** - Defines account validation structs
4. **`#[account]`** - Defines custom account types
5. **`#[error_code]`** - Defines custom error enums
6. **`#[event]`** - Defines event structs for logging

### declare_id! Macro

```rust
use anchor_lang::prelude::*;

// Program ID from /target/deploy/program_name.json
declare_id!("11111111111111111111111111111111");
```

Sync program IDs after building:

```bash
anchor keys sync
```

### #[program] Macro

Marks the module containing instruction handlers:

```rust
#[program]
pub mod my_program {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, data: u64) -> Result<()> {
        ctx.accounts.new_account.data = data;
        msg!("Data set to: {}!", data);
        Ok(())
    }

    pub fn update(ctx: Context<Update>, new_data: u64) -> Result<()> {
        ctx.accounts.account.data = new_data;
        Ok(())
    }
}
```

**Context<T> provides:**
- `ctx.accounts` - Validated accounts (type T)
- `ctx.program_id` - Current program's ID
- `ctx.remaining_accounts` - Additional accounts not in struct
- `ctx.bumps` - PDA bump seeds (struct with fields matching PDA account names)

### #[derive(Accounts)] Macro

Defines account validation structs:

```rust
#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = signer, space = 8 + 8)]
    pub new_account: Account<'info, NewAccount>,

    #[account(mut)]
    pub signer: Signer<'info>,

    pub system_program: Program<'info, System>,
}
```

**Validation happens in two ways:**
1. **Account Types** - Signer, Account<'info, T>, Program<'info, T>, etc.
2. **Account Constraints** - `#[account(...)]` attribute constraints

### #[account] Macro

Defines custom account data structures:

```rust
#[account]
pub struct NewAccount {
    pub data: u64,      // 8 bytes
    pub owner: Pubkey,  // 32 bytes
    pub bump: u8,       // 1 byte
}
```

**Automatically implements:**
- Account discriminator (first 8 bytes)
- Serialization/deserialization (Borsh)
- Owner validation (owned by program)

**Account discriminator** = first 8 bytes of SHA256(`"account:NewAccount"`)

### #[error_code] Macro

Defines custom program errors:

```rust
#[error_code]
pub enum ErrorCode {
    #[msg("Amount must be greater than zero")]
    InvalidAmount,

    #[msg("Insufficient funds")]
    InsufficientFunds,
}
```

Usage:

```rust
require!(amount > 0, ErrorCode::InvalidAmount);
```

### #[event] Macro

Defines event structs for logging:

```rust
#[event]
pub struct TransferEvent {
    pub from: Pubkey,
    pub to: Pubkey,
    pub amount: u64,
}

// Emit via program logs
pub fn transfer(ctx: Context<Transfer>, amount: u64) -> Result<()> {
    emit!(TransferEvent {
        from: ctx.accounts.from.key(),
        to: ctx.accounts.to.key(),
        amount,
    });
    Ok(())
}
```

---

## Program Structure

### Complete Example

```rust
use anchor_lang::prelude::*;

declare_id!("YourProgramIdHere11111111111111111111111");

#[program]
mod my_program {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, data: u64) -> Result<()> {
        ctx.accounts.new_account.data = data;
        ctx.accounts.new_account.authority = ctx.accounts.authority.key();
        Ok(())
    }

    pub fn update(ctx: Context<Update>, new_data: u64) -> Result<()> {
        ctx.accounts.account.data = new_data;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = authority, space = 8 + 8 + 32)]
    pub new_account: Account<'info, MyAccount>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Update<'info> {
    #[account(
        mut,
        has_one = authority
    )]
    pub account: Account<'info, MyAccount>,

    pub authority: Signer<'info>,
}

#[account]
pub struct MyAccount {
    pub data: u64,
    pub authority: Pubkey,
}
```

### Space Calculation

Use `InitSpace` derive macro:

```rust
#[account]
#[derive(InitSpace)]
pub struct MyAccount {
    pub data: u64,                    // 8 bytes
    #[max_len(50)]
    pub name: String,                 // 4 + 50 bytes
    pub authority: Pubkey,            // 32 bytes
}

// INIT_SPACE = 8 + 4 + 50 + 32 = 94 bytes

#[account(init, payer = payer, space = 8 + MyAccount::INIT_SPACE)]
pub account: Account<'info, MyAccount>,
```

**Space = 8 (discriminator) + account data size**

---

## Account Validation Constraints

### Common Constraints

#### init - Create New Account

```rust
#[account(
    init,
    payer = payer,
    space = 8 + 8
)]
pub new_account: Account<'info, Counter>,
```

#### init_if_needed - Create if Doesn't Exist

```rust
#[account(
    init_if_needed,
    payer = payer,
    space = 8 + 8
)]
pub account: Account<'info, Counter>,
```

Requires `init-if-needed` feature in Cargo.toml:

```toml
[dependencies]
anchor-lang = { version = "0.32.1", features = ["init-if-needed"] }
```

#### mut - Mutable Account

```rust
#[account(mut)]
pub account: Account<'info, Counter>,
```

#### signer - Requires Signature

```rust
#[account(signer)]
pub authority: AccountInfo<'info>,
// Or use Signer<'info> type
pub authority: Signer<'info>,
```

#### close - Close Account

```rust
#[account(
    mut,
    close = receiver  // Send lamports to receiver
)]
pub account_to_close: Account<'info, MyAccount>,

#[account(mut)]
pub receiver: SystemAccount<'info>,
```

### PDA Constraints

#### seeds + bump - Validate PDA

```rust
#[account(
    seeds = [b"vault", authority.key().as_ref()],
    bump
)]
pub vault: Account<'info, Vault>,
```

Access bump in instruction:

```rust
pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    let bump = ctx.bumps.vault;
    ctx.accounts.vault.bump = bump;
    Ok(())
}
```

#### seeds + bump + init - Create PDA Account

```rust
#[account(
    init,
    payer = payer,
    space = 8 + 32 + 1,
    seeds = [b"vault", authority.key().as_ref()],
    bump
)]
pub vault: Account<'info, Vault>,
```

### Validation Constraints

#### has_one - Field Matches Account

```rust
#[account(
    mut,
    has_one = authority  // Checks account.authority == authority.key()
)]
pub account: Account<'info, MyAccount>,
pub authority: Signer<'info>,
```

#### address - Matches Specific Address

```rust
#[account(address = admin_pubkey)]
pub admin: Signer<'info>,
```

#### owner - Validates Owner Program

```rust
#[account(owner = token::ID)]
pub token_account: AccountInfo<'info>,
```

#### constraint - Custom Validation

```rust
#[account(
    constraint = account.data > 0 @ ErrorCode::InvalidData
)]
pub account: Account<'info, MyAccount>,
```

### Token Constraints

#### mint - Create/Validate Mint

```rust
use anchor_spl::token_interface::{Mint, TokenInterface};

#[account(
    init,
    payer = payer,
    mint::decimals = 6,
    mint::authority = mint_authority,
    mint::freeze_authority = mint_authority,
)]
pub mint: InterfaceAccount<'info, Mint>,
pub token_program: Interface<'info, TokenInterface>,
```

#### token - Create/Validate Token Account

```rust
use anchor_spl::token_interface::{TokenAccount, TokenInterface};

#[account(
    init,
    payer = payer,
    token::mint = mint,
    token::authority = owner,
    token::token_program = token_program,
    seeds = [b"vault"],
    bump
)]
pub vault: InterfaceAccount<'info, TokenAccount>,
```

#### associated_token - Create/Validate ATA

```rust
use anchor_spl::{
    associated_token::AssociatedToken,
    token_interface::{Mint, TokenAccount, TokenInterface},
};

#[account(
    init,
    payer = payer,
    associated_token::mint = mint,
    associated_token::authority = owner,
    associated_token::token_program = token_program,
)]
pub token_account: InterfaceAccount<'info, TokenAccount>,

pub mint: InterfaceAccount<'info, Mint>,
pub owner: SystemAccount<'info>,
pub token_program: Interface<'info, TokenInterface>,
pub associated_token_program: Program<'info, AssociatedToken>,
pub system_program: Program<'info, System>,
```

---

## IDL (Interface Description Language)

### What is the IDL?

The IDL is a JSON file describing your program's interface:
- Instructions (name, accounts, arguments)
- Account types (structs)
- Custom types (enums, type aliases)
- Events
- Errors
- Discriminators

### IDL Generation

Enable IDL build feature in `Cargo.toml`:

```toml
[features]
idl-build = ["anchor-lang/idl-build"]
```

Build program and generate IDL:

```bash
anchor build        # Builds program + IDL
anchor idl build    # Only builds IDL
```

IDL output location: `target/idl/<program_name>.json`

### IDL Structure Example

```json
{
  "address": "8HupNBr7SBhBLcBsLhbtes3tCarBm6Bvpqp5AfVjHuj8",
  "metadata": {
    "name": "example",
    "version": "0.1.0",
    "spec": "0.1.0"
  },
  "instructions": [
    {
      "name": "initialize",
      "discriminator": [175, 175, 109, 31, 13, 152, 155, 237],
      "accounts": [
        {
          "name": "new_account",
          "writable": true,
          "signer": true
        },
        {
          "name": "signer",
          "writable": true,
          "signer": true
        },
        {
          "name": "system_program",
          "address": "11111111111111111111111111111111"
        }
      ],
      "args": [
        {
          "name": "data",
          "type": "u64"
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "NewAccount",
      "discriminator": [123, 45, 67, 89, 101, 112, 131, 145]
    }
  ],
  "types": [
    {
      "name": "NewAccount",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "data",
            "type": "u64"
          }
        ]
      }
    }
  ]
}
```

### Instruction Discriminator

8-byte identifier for each instruction:

```
discriminator = SHA256("global:initialize")[0..8]
```

Automatically handled by Anchor client.

### Account Discriminator

8-byte identifier for each account type:

```
discriminator = SHA256("account:NewAccount")[0..8]
```

Used for:
- Account type verification on deserialization
- Type safety checks

### IDL Deployment

Deploy IDL on-chain:

```bash
anchor deploy              # Deploys program + IDL
anchor deploy --no-idl     # Deploy program only
anchor idl init <PROGRAM_ID> -f target/idl/program.json
```

Fetch IDL from chain:

```bash
anchor idl fetch <PROGRAM_ID>
```

---

## TypeScript Client

### Installation

```bash
npm install @coral-xyz/anchor @solana/web3.js
# or
yarn add @coral-xyz/anchor @solana/web3.js
```

> **Legacy dependency:** Anchor's TS client requires `@solana/web3.js` v1 as a peer dependency. This is the only reason to install web3.js - it is in maintenance mode. For non-Anchor client code, use [`@solana/kit`](https://solanakit.org) instead. Use [`@solana/compat`](https://www.npmjs.com/package/@solana/compat) to bridge between Kit and legacy web3.js types when needed.
>
> **For new dApps:** Use framework-kit (`@solana/client` + `@solana/react-hooks`) instead of `@solana/wallet-adapter-react` for wallet connections. Anchor's `.methods()` API works with either approach. See [client-development.md](client-development.md).

### Setup Program Instance

#### With Wallet (Frontend)

> **Legacy pattern** - uses `@solana/wallet-adapter-react`. For new projects, use framework-kit for wallet management. See [client-development.md](client-development.md). The Anchor `.methods()` API below works the same regardless.

```typescript
import { Program, AnchorProvider, setProvider } from "@coral-xyz/anchor";
import { useAnchorWallet, useConnection } from "@solana/wallet-adapter-react";
import type { MyProgram } from "./types/my_program";
import idl from "./idl/my_program.json";

const { connection } = useConnection();
const wallet = useAnchorWallet();

const provider = new AnchorProvider(connection, wallet, {});
setProvider(provider);

const program = new Program(idl as MyProgram, { connection });
```

#### Without Wallet (Read-Only)

```typescript
import { Connection, PublicKey } from "@solana/web3.js";
import { Program } from "@coral-xyz/anchor";
import idl from "./idl/my_program.json";

const connection = new Connection("https://api.devnet.solana.com");
const program = new Program(idl, { connection });
```

### Invoke Instructions

#### Using .rpc() - Send Transaction

```typescript
import { Keypair, SystemProgram } from "@solana/web3.js";
import BN from "bn.js";

const newAccountKp = new Keypair();
const data = new BN(42);

const txSignature = await program.methods
  .initialize(data)
  .accounts({
    newAccount: newAccountKp.publicKey,
    signer: wallet.publicKey,
    systemProgram: SystemProgram.programId,
  })
  .signers([newAccountKp])
  .rpc();

console.log("Transaction:", txSignature);
```

#### Using .instruction() - Build Instruction

```typescript
const ix = await program.methods
  .initialize(data)
  .accounts({
    newAccount: newAccountKp.publicKey,
    signer: wallet.publicKey,
    systemProgram: SystemProgram.programId,
  })
  .instruction();

// Add to transaction
const tx = new Transaction().add(ix);
```

#### Using .transaction() - Build Transaction

```typescript
const tx = await program.methods
  .initialize(data)
  .accounts({ /* ... */ })
  .transaction();

// Sign and send
tx.recentBlockhash = (await connection.getLatestBlockhash()).blockhash;
tx.sign(wallet, newAccountKp);
const signature = await connection.sendRawTransaction(tx.serialize());
```

### Fetch Accounts

#### Fetch Single Account

```typescript
const accountData = await program.account.myAccount.fetch(accountPubkey);
console.log("Data:", accountData.data.toString());
```

#### Fetch All Accounts

```typescript
const accounts = await program.account.myAccount.all();
accounts.forEach((account) => {
  console.log("Pubkey:", account.publicKey.toString());
  console.log("Data:", account.account.data);
});
```

#### Fetch with Filters

```typescript
const accounts = await program.account.myAccount.all([
  {
    memcmp: {
      offset: 8,  // After discriminator
      bytes: authority.toBase58(),
    },
  },
]);
```

### Event Listeners

```typescript
const listenerId = program.addEventListener(
  "TransferEvent",
  (event, slot) => {
    console.log("From:", event.from.toString());
    console.log("To:", event.to.toString());
    console.log("Amount:", event.amount.toString());
  }
);

// Remove listener
program.removeEventListener(listenerId);
```

---

## Rust Client

### Dependencies

Add to `Cargo.toml`:

```toml
[dependencies]
anchor-client = { version = "0.32.1", features = ["async"] }
anchor-lang = "0.32.1"
solana-sdk = "2.3.0"
tokio = { version = "1.0", features = ["full"] }
```

### Generate Client with declare_program!

Place IDL in `/idls/program_name.json`:

```rust
use anchor_lang::prelude::*;

declare_program!(example);
use example::{
    accounts::Counter,
    client::{accounts, args},
};
```

### Example Client

```rust
use anchor_client::{
    solana_client::rpc_client::RpcClient,
    solana_sdk::{
        commitment_config::CommitmentConfig,
        signature::Keypair,
        signer::Signer,
        system_program,
    },
    Client, Cluster,
};
use std::rc::Rc;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let connection = RpcClient::new_with_commitment(
        "http://127.0.0.1:8899",
        CommitmentConfig::confirmed(),
    );

    let payer = Keypair::new();
    let counter = Keypair::new();

    // Create program client
    let provider = Client::new_with_options(
        Cluster::Localnet,
        Rc::new(payer),
        CommitmentConfig::confirmed(),
    );
    let program = provider.program(example::ID)?;

    // Build instruction
    let ix = program
        .request()
        .accounts(accounts::Initialize {
            counter: counter.pubkey(),
            payer: program.payer(),
            system_program: system_program::ID,
        })
        .args(args::Initialize)
        .instructions()?
        .remove(0);

    // Send transaction
    let signature = program
        .request()
        .instruction(ix)
        .signer(&counter)
        .send()
        .await?;

    println!("Transaction: {}", signature);

    // Fetch account
    let account: Counter = program.account::<Counter>(counter.pubkey()).await?;
    println!("Count: {}", account.count);

    Ok(())
}
```

---

## Anchor CLI Commands

### Project Commands

```bash
# Initialize new project
anchor init my-project
anchor init my-project --test-template rust  # Rust tests
anchor init my-project --test-template mollusk  # Mollusk tests

# Create new program in workspace
anchor new my-program
```

### Build Commands

```bash
# Build all programs
anchor build

# Build specific program
anchor build --program-name my-program

# Build without IDL generation
anchor build --no-idl

# Verifiable build (uses solana-verify)
anchor build --verifiable
```

### Deploy Commands

```bash
# Deploy to cluster in Anchor.toml
anchor deploy

# Deploy specific program
anchor deploy --program-name my-program

# Deploy without IDL
anchor deploy --no-idl

# Deploy with additional program args
anchor deploy -- --max-len 200000
```

### Test Commands

```bash
# Build + deploy + test
anchor test

# Skip local validator (use running validator)
anchor test --skip-local-validator

# Test specific program
anchor test --program-name my-program

# Skip IDL build
anchor test --no-idl
```

### IDL Commands

```bash
# Build IDL only
anchor idl build

# Initialize IDL on-chain
anchor idl init <PROGRAM_ID> -f target/idl/program.json

# Fetch IDL from chain
anchor idl fetch <PROGRAM_ID>

# Upgrade on-chain IDL
anchor idl upgrade <PROGRAM_ID> -f target/idl/program.json

# Get IDL authority
anchor idl authority <PROGRAM_ID>

# Set new IDL authority
anchor idl set-authority <PROGRAM_ID> --new-authority <NEW_AUTHORITY>
```

### Other Commands

```bash
# Sync program IDs
anchor keys sync

# List program keypairs
anchor keys list

# Expand macros
anchor expand
anchor expand --program-name my-program

# Verify deployed program
anchor verify -p <program-name> <PROGRAM_ID>

# Run migration script
anchor migrate

# Close deployed program (reclaim rent)
solana program close <PROGRAM_ID>
```

### Local Validator

```bash
# Start local validator
solana-test-validator

# Start with program loaded
solana-test-validator --bpf-program <PROGRAM_ID> target/deploy/program.so

# Configure in Anchor.toml
[test.validator]
url = "https://api.devnet.solana.com"

[[test.validator.clone]]
address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # Clone USDC mint
```

---

## Token Integration (anchor-spl)

### Dependencies

```toml
[dependencies]
anchor-spl = { version = "0.32.1", features = ["metadata"] }
```

### Token Interface (Token + Token-2022)

Use `token_interface` for compatibility with both Token Program and Token Extensions:

```rust
use anchor_spl::token_interface::{
    self, Mint, MintTo, TokenAccount, TokenInterface, TransferChecked
};
```

### Create Mint

```rust
#[derive(Accounts)]
pub struct CreateMint<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        init,
        payer = payer,
        mint::decimals = 6,
        mint::authority = mint_authority,
    )]
    pub mint: InterfaceAccount<'info, Mint>,

    /// CHECK: Mint authority
    pub mint_authority: UncheckedAccount<'info>,

    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}
```

### Create Token Account (ATA)

```rust
use anchor_spl::associated_token::AssociatedToken;

#[derive(Accounts)]
pub struct CreateTokenAccount<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        init,
        payer = payer,
        associated_token::mint = mint,
        associated_token::authority = owner,
        associated_token::token_program = token_program,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    pub mint: InterfaceAccount<'info, Mint>,
    pub owner: SystemAccount<'info>,
    pub token_program: Interface<'info, TokenInterface>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
}
```

### Mint Tokens

```rust
pub fn mint_tokens(ctx: Context<MintTokens>, amount: u64) -> Result<()> {
    let cpi_accounts = MintTo {
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.token_account.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_context = CpiContext::new(cpi_program, cpi_accounts);

    token_interface::mint_to(cpi_context, amount)?;
    Ok(())
}
```

### Transfer Tokens

```rust
pub fn transfer_tokens(ctx: Context<TransferTokens>, amount: u64) -> Result<()> {
    let decimals = ctx.accounts.mint.decimals;

    let cpi_accounts = TransferChecked {
        from: ctx.accounts.from.to_account_info(),
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.to.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_context = CpiContext::new(cpi_program, cpi_accounts);

    token_interface::transfer_checked(cpi_context, amount, decimals)?;
    Ok(())
}
```

### PDA as Token Authority

```rust
#[derive(Accounts)]
pub struct MintWithPDA<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        init,
        payer = payer,
        mint::decimals = 6,
        mint::authority = mint,  // PDA is authority
        seeds = [b"mint"],
        bump
    )]
    pub mint: InterfaceAccount<'info, Mint>,

    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

pub fn mint_with_pda(ctx: Context<MintWithPDA>, amount: u64) -> Result<()> {
    let seeds = &[b"mint".as_ref(), &[ctx.bumps.mint]];
    let signer_seeds = &[&seeds[..]];

    let cpi_accounts = MintTo {
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.token_account.to_account_info(),
        authority: ctx.accounts.mint.to_account_info(),
    };

    let cpi_context = CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        cpi_accounts
    ).with_signer(signer_seeds);

    token_interface::mint_to(cpi_context, amount)?;
    Ok(())
}
```

---

## Testing with Anchor

### TypeScript Tests (Default)

Test file location: `tests/my-program.ts`

```typescript
import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { MyProgram } from "../target/types/my_program";
import { expect } from "chai";

describe("my-program", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.MyProgram as Program<MyProgram>;

  it("Initializes account", async () => {
    const newAccount = anchor.web3.Keypair.generate();

    await program.methods
      .initialize(new anchor.BN(42))
      .accounts({
        newAccount: newAccount.publicKey,
        signer: provider.wallet.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .signers([newAccount])
      .rpc();

    const account = await program.account.myAccount.fetch(
      newAccount.publicKey
    );
    expect(account.data.toNumber()).to.equal(42);
  });
});
```

### Rust Tests with LiteSVM

Initialize project with Rust tests:

```bash
anchor init my-project --test-template rust
```

Test file: `tests/src/test_initialize.rs`

```rust
use anchor_client::anchor_lang::prelude::*;
use anchor_client::anchor_lang::solana_program::system_program;
use anchor_lang_lite_svm::LiteSVM;

#[test]
fn test_initialize() {
    let mut svm = LiteSVM::new();

    let program_id = svm.deploy_program("target/deploy/my_program.so");
    let payer = Keypair::new();
    let counter = Keypair::new();

    svm.airdrop(&payer.pubkey(), 10_000_000_000).unwrap();

    let ix = my_program::instruction::Initialize {
        new_account: counter.pubkey(),
        signer: payer.pubkey(),
        system_program: system_program::ID,
    };

    let tx = svm.send_transaction(vec![ix], &[&payer, &counter]).unwrap();

    // Fetch and verify account
    let account_data = svm.get_account(&counter.pubkey()).unwrap();
    // Verify data...
}
```

### Test Configuration (Anchor.toml)

```toml
[test]
# Startup timeout for validator
startup_wait = 10000

[test.validator]
# URL to clone accounts from
url = "https://api.mainnet-beta.solana.com"

# Clone accounts
[[test.validator.clone]]
address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Load account from JSON
[[test.validator.account]]
address = "MyAccount111111111111111111111111111111111"
filename = "tests/fixtures/my-account.json"

# Set program as upgradeable
[test.validator.upgradeable]
my_program = true
```

---

## Anchor Features

### Custom Errors

```rust
#[error_code]
pub enum ErrorCode {
    #[msg("Amount must be greater than zero")]
    InvalidAmount,

    #[msg("Authority mismatch")]
    Unauthorized,
}

// Usage
require!(amount > 0, ErrorCode::InvalidAmount);
require_keys_eq!(account.owner, authority.key(), ErrorCode::Unauthorized);
```

**Error macros:**
- `require!(condition, error)` - Condition must be true
- `require_eq!(a, b, error)` - Values must be equal
- `require_neq!(a, b, error)` - Values must not be equal
- `require_keys_eq!(a, b, error)` - Pubkeys must match
- `require_keys_neq!(a, b, error)` - Pubkeys must not match
- `require_gt!(a, b, error)` - a > b
- `require_gte!(a, b, error)` - a >= b

### Events

#### emit! (Program Logs)

```rust
#[event]
pub struct TransferEvent {
    pub from: Pubkey,
    pub to: Pubkey,
    pub amount: u64,
}

pub fn transfer(ctx: Context<Transfer>, amount: u64) -> Result<()> {
    emit!(TransferEvent {
        from: ctx.accounts.from.key(),
        to: ctx.accounts.to.key(),
        amount,
    });
    Ok(())
}
```

#### emit_cpi! (CPI Data)

Enable feature:

```toml
[dependencies]
anchor-lang = { version = "0.32.1", features = ["event-cpi"] }
```

Usage:

```rust
#[event_cpi]
#[derive(Accounts)]
pub struct EmitEvent {}

pub fn emit_event(ctx: Context<EmitEvent>, msg: String) -> Result<()> {
    emit_cpi!(CustomEvent { message: msg });
    Ok(())
}
```

### Zero-Copy Accounts

For large accounts (>10KB):

```toml
[dependencies]
bytemuck = { version = "1.20.0", features = ["min_const_generics"] }
```

```rust
#[account(zero_copy)]
pub struct LargeData {
    pub data: [u8; 10000],
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + std::mem::size_of::<LargeData>()
    )]
    pub large_account: AccountLoader<'info, LargeData>,

    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    let mut large_account = ctx.accounts.large_account.load_init()?;
    large_account.data[0] = 42;
    Ok(())
}

pub fn update(ctx: Context<Update>) -> Result<()> {
    let mut large_account = ctx.accounts.large_account.load_mut()?;
    large_account.data[0] = 100;
    Ok(())
}
```

**For >10240 bytes**, use `zero` constraint + create account separately:

```rust
#[account(zero)]  // Instead of init
pub large_account: AccountLoader<'info, LargeData>,
```

### declare_program! (Dependency-Free CPI)

Place IDL in `/idls/program_name.json`:

```rust
declare_program!(example);

use example::{
    accounts::Counter,
    cpi::{self, accounts::Initialize},
    program::Example,
};

// CPI to other program
pub fn call_example(ctx: Context<CallExample>) -> Result<()> {
    let cpi_ctx = CpiContext::new(
        ctx.accounts.example_program.to_account_info(),
        Initialize {
            counter: ctx.accounts.counter.to_account_info(),
            payer: ctx.accounts.payer.to_account_info(),
            system_program: ctx.accounts.system_program.to_account_info(),
        },
    );

    cpi::initialize(cpi_ctx)?;
    Ok(())
}
```

---

## Common Patterns

### Store Bump Seed

```rust
#[account]
pub struct Vault {
    pub authority: Pubkey,
    pub bump: u8,
}

pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    ctx.accounts.vault.authority = ctx.accounts.authority.key();
    ctx.accounts.vault.bump = ctx.bumps.vault;
    Ok(())
}

// Use stored bump
let seeds = &[
    b"vault",
    ctx.accounts.vault.authority.as_ref(),
    &[ctx.accounts.vault.bump]
];
```

### Multi-Seed PDAs

```rust
#[account(
    init,
    payer = payer,
    space = 8 + UserAccount::INIT_SPACE,
    seeds = [
        b"user",
        user.key().as_ref(),
        &counter.to_le_bytes()
    ],
    bump
)]
pub user_account: Account<'info, UserAccount>,
```

### CPI with PDA Signer

```rust
pub fn transfer_with_pda(ctx: Context<Transfer>, amount: u64) -> Result<()> {
    let seeds = &[
        b"vault",
        &[ctx.bumps.vault]
    ];
    let signer_seeds = &[&seeds[..]];

    let cpi_accounts = TransferChecked {
        from: ctx.accounts.from.to_account_info(),
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.to.to_account_info(),
        authority: ctx.accounts.vault.to_account_info(),
    };

    let cpi_ctx = CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        cpi_accounts
    ).with_signer(signer_seeds);

    token_interface::transfer_checked(cpi_ctx, amount, decimals)?;
    Ok(())
}
```

### Remaining Accounts

```rust
pub fn process_multiple(ctx: Context<Process>) -> Result<()> {
    for account_info in ctx.remaining_accounts.iter() {
        let account = Account::<SomeAccount>::try_from(account_info)?;
        msg!("Processing: {}", account_info.key());
        // Process account...
    }
    Ok(())
}

#[derive(Accounts)]
pub struct Process<'info> {
    pub authority: Signer<'info>,
    // Additional accounts in remaining_accounts
}
```

### Close Account Pattern

```rust
#[derive(Accounts)]
pub struct CloseAccount<'info> {
    #[account(
        mut,
        close = receiver,  // Sends lamports to receiver
        has_one = authority
    )]
    pub account: Account<'info, MyAccount>,

    pub authority: Signer<'info>,

    #[account(mut)]
    /// CHECK: Receives lamports
    pub receiver: UncheckedAccount<'info>,
}
```

### Dynamic Account Space

```rust
#[derive(Accounts)]
#[instruction(name: String)]
pub struct Create<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + 4 + name.len() + 8
    )]
    pub item: Account<'info, Item>,

    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Item {
    pub name: String,
    pub count: u64,
}
```

---

## Error Handling

### Built-in Anchor Errors

Anchor provides built-in errors in `ErrorCode` enum. Examples:
- `ConstraintHasOne` - has_one constraint failed
- `ConstraintSigner` - Account not a signer
- `ConstraintMut` - Account not mutable
- `ConstraintSeeds` - Seeds constraint failed
- `AccountNotInitialized` - Account discriminator is zero

### Custom Error Implementation

```rust
#[error_code]
pub enum ErrorCode {
    #[msg("Amount must be greater than zero")]
    InvalidAmount,

    #[msg("Insufficient balance: required {}, available {}")]
    InsufficientBalance,

    #[msg("Unauthorized access")]
    Unauthorized,
}

pub fn validate_amount(ctx: Context<Validate>, amount: u64) -> Result<()> {
    require!(amount > 0, ErrorCode::InvalidAmount);

    require!(
        ctx.accounts.account.balance >= amount,
        ErrorCode::InsufficientBalance
    );

    require_keys_eq!(
        ctx.accounts.account.owner,
        ctx.accounts.authority.key(),
        ErrorCode::Unauthorized
    );

    Ok(())
}
```

### Error Numbers

Anchor errors use this numbering:
- `0-1000` - Internal Anchor errors
- `1000-2000` - Reserved
- `2000-3000` - Custom program errors (from #[error_code])
- `3000+` - Additional custom errors

### TypeScript Error Handling

```typescript
try {
  await program.methods
    .transfer(amount)
    .accounts({ /* ... */ })
    .rpc();
} catch (error) {
  if (error.code === 6000) {  // Custom error code
    console.log("Custom error:", error.msg);
  }
  console.log("Error logs:", error.logs);
}
```

---

## Anchor.toml Configuration

```toml
[toolchain]
anchor_version = "0.32.1"
solana_version = "2.3.0"

[features]
resolution = true  # IDL account resolution
seeds = false
skip-lint = false

[programs.localnet]
my_program = "YourProgramIdHere11111111111111111111111"

[programs.devnet]
my_program = "YourProgramIdHere11111111111111111111111"

[programs.mainnet]
my_program = "YourProgramIdHere11111111111111111111111"

[provider]
cluster = "localnet"  # or devnet, mainnet-beta
wallet = "~/.config/solana/id.json"

[scripts]
test = "yarn run ts-mocha -p ./tsconfig.json -t 1000000 tests/**/*.ts"

[test]
startup_wait = 10000

[test.validator]
url = "https://api.devnet.solana.com"

[[test.validator.clone]]
address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

[test.validator.upgradeable]
my_program = true

[workspace]
types = "app/src/idl/"
members = ["programs/*"]

package_manager = "yarn"  # npm, yarn, pnpm, bun
```

---

## Additional Resources

- **Official Docs**: https://www.anchor-lang.com
- **GitHub**: https://github.com/coral-xyz/anchor
- **Examples**: https://github.com/coral-xyz/anchor/tree/master/tests
- **Discord**: https://discord.gg/anchor

For general Solana concepts (accounts, PDAs, CPIs, transactions, etc.), refer to other reference files in this directory.
