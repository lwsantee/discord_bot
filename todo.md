# Features 

- [ ] cache access token, so you can skip logging in everytime the bot starts
  - [ ] related: investigate refreshing the access token
- [ ] get control functions (skip, pause, etc) working 
- [x] make bot leave if alone in the channel for some time

# Fixes 

- [x] .play command seems to append the entire existing queue followed by the requested song
- [x] potentially move references to the name 'Discord Bot' into an env var to allow customizing the bot name
- [x] break authentication server out into separate microservice
- [ ] make errors relating to being logged out more obvious
- [x] get docker builds on arm64 working
- [ ] pause keeps streaming, then dumps all data rapidly when unpaused
