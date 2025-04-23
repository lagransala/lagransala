{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        nixpkgs.follows = "nixpkgs";
      };
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  outputs =
    { self, nixpkgs, uv2nix, pyproject-nix, pyproject-build-systems, ... }:
    let
      inherit (nixpkgs) lib;

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

      pyprojectOverrides = final: prev: {
        lagransala = prev.lagransala.overrideAttrs (old: {
          nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [
            (final.resolveBuildSystem {
              hatchling = [ ];
              editables = [ ];
            })
          ];
          # Add necessary overrides
          # https://pyproject-nix.github.io/uv2nix/overriding/index.html
        });
        pyperclip = prev.pyperclip.overrideAttrs (old: {
          nativeBuildInputs = old.nativeBuildInputs
            ++ [ (final.resolveBuildSystem { setuptools = [ ]; }) ];
        });
        litellm = prev.litellm.overrideAttrs (old: {
          nativeBuildInputs = old.nativeBuildInputs
            ++ [ (final.resolveBuildSystem { "poetry-core" = [ ]; }) ];
        });
        faust-cchardet = prev.faust-cchardet.overrideAttrs (old: {
          preferWheels = true;
          nativeBuildInputs = old.nativeBuildInputs ++ [
            (final.resolveBuildSystem {
              setuptools = [ ];
              wheel = [ ];
              cython = [ ];
            })
          ];
        });
      };

      pkgs = nixpkgs.legacyPackages.x86_64-linux;

      python = pkgs.python313;

      pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
        inherit python;
      }).overrideScope (lib.composeManyExtensions [
        pyproject-build-systems.overlays.default
        overlay
        pyprojectOverrides
      ]);

    in {
      packages.x86_64-linux.default =
        pythonSet.mkVirtualEnv "lagransala-env" workspace.deps.default;

      apps.x86_64-linux = {
        default = {
          type = "app";
          program = "${self.packages.x86_64-linux.default}/bin/lagransala";
        };
      };

      # This example provides two different modes of development:
      # - Impurely using uv to manage virtual environments
      # - Pure development using uv2nix to manage virtual environments
      devShells.x86_64-linux = let
        impure = pkgs.mkShell {
          packages = [ python pkgs.uv ];
          env = {
            UV_PYTHON_DOWNLOADS = "never";
            UV_PYTHON = python.interpreter;
          } // lib.optionalAttrs pkgs.stdenv.isLinux {
            LD_LIBRARY_PATH =
              lib.makeLibraryPath pkgs.pythonManylinuxPackages.manylinux1;
          };
          shellHook = ''
            unset PYTHONPATH
          '';
        };
        uv2nix = let
          # Create an overlay enabling editable mode for all local dependencies.
          editableOverlay = workspace.mkEditablePyprojectOverlay {
            root = "$REPO_ROOT";
            members = [ "lagransala" ];
          };

          editablePythonSet = pythonSet.overrideScope
            (lib.composeManyExtensions [
              editableOverlay

              # Apply fixups for building an editable package of your workspace packages
              (final: prev: {
                lagransala = prev.lagransala.overrideAttrs (old: {
                  # It's a good idea to filter the sources going into an editable build
                  # so the editable package doesn't have to be rebuilt on every change.
                  src = lib.fileset.toSource {
                    root = old.src;
                    fileset = lib.fileset.unions [
                      (old.src + "/pyproject.toml")
                      (old.src + "/README.md")
                      (old.src + "/src/lagransala/__init__.py")
                    ];
                  };

                  nativeBuildInputs = old.nativeBuildInputs
                    ++ final.resolveBuildSystem { editables = [ ]; };
                });

              })
            ]);

          virtualenv = (editablePythonSet.mkVirtualEnv "lagransala-dev-env"
            workspace.deps.all).overrideAttrs
            (old: { venvIgnoreCollisions = [ "*" ]; });

        in pkgs.mkShell {
          packages = [ virtualenv pkgs.uv ];

          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = "${virtualenv}/bin/python";
            UV_PYTHON_DOWNLOADS = "never";
          };

          shellHook = ''
            unset PYTHONPATH
            export REPO_ROOT=$(git rev-parse --show-toplevel)
          '';
        };
      in {
        inherit impure uv2nix;
        default = uv2nix;
      };
    };
}
