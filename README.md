# homebrew-smplify

Homebrew tap for the [Smplify CLI](https://cli.smplify.com).

```sh
brew tap smplify-mdm/smplify
brew trust --cask smplify-mdm/smplify/smplify
brew install --cask smplify
```

`brew trust` is required on Homebrew 6.0 and later, which refuses to load
casks from a non-official tap until they are explicitly trusted. It is a
one-time action per machine.

`Casks/smplify.rb` is generated and committed by the CLI release pipeline on
each release tag; do not edit it by hand.

Not on `homebrew/homebrew-core`, so a bare `brew install smplify` will not
resolve — the tap is required.
