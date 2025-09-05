# Features 

- [ ] cache access token, so you can skip logging in everytime the bot starts
  - [ ] related: investigate refreshing the access token
- [ ] get control functions (skip, pause, etc) working 

# Fixes 

- [x] .play command seems to append the entire existing queue followed by the requested song
- [x] potentially move references to the name 'Discord Bot' into an env var to allow customizing the bot name
- [ ] break authentication server out into separate microservice
- [ ] make errors relating to being logged out more obvious
