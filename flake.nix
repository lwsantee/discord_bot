{
  description = "Python dev env for crisisbot";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }: 
    flake-utils.lib.eachDefaultSystem (system:
      let 
        pkgs = import nixpkgs { inherit system; };
        python-pkgs = with pkgs.python312Packages; [ discordpy python-dotenv yt-dlp google-api-python-client ];
      in {
        devShell = pkgs.mkShell {
          packages = with pkgs; [ python312 ] ++ python-pkgs;
        };
      });
}
