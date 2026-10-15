{
  description = "La Gran Sala development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      # Python packages are managed by uv. Nix only provides the interpreter, uv
      # and the shared libraries that the prebuilt wheels expect to find.
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.python313
            pkgs.uv
          ];

          env = {
            UV_PYTHON_DOWNLOADS = "never";
            UV_PYTHON = pkgs.python313.interpreter;
            # libstdc++ is needed by tokenizers (litellm), zlib by several wheels.
            LD_LIBRARY_PATH = lib.makeLibraryPath [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib
            ];
          };

          shellHook = ''
            unset PYTHONPATH
          '';
        };
      });
    };
}
