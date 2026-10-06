# Buzz

A workspace where humans and agents build together, on a relay you own.
https://github.com/block/buzz/tree/main


## Nostr keypair

Now you need an owner Nostr keypair. The owner is the admin of the
workspace. Set the key to `dapp_buzz_relay_owner_pubkey` variable.

Here are two ways to generate one:

### Desktop App

This method keeps the private key on your device — it never touches the server.

- Download the Buzz desktop app
- On first launch, click “Create a new identity key”
- The app generates a Nostr keypair and stores it locally
- Copy your public key (it starts with npub1...)
- Convert the npub to hex — you can use this one-liner:

```bash
npx @cmdcode/nip19 decode npub1yourkeyhere
```

The hex output is what you set as `RELAY_OWNER_PUBKEY` (64-char hex, no npub prefix)


### buzz-admin CLI

If you prefer to generate the key on the server:

```bash
# Run inside the relay container after first start
docker compose exec relay buzz-admin generate-key
```

This gives you a hex pubkey and private key. Save the private key
somewhere safe — you’ll need it for the desktop app.

