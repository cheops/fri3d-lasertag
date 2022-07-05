Minimum Viable Product

# vocabulary
- round: 1 cycle of practicing (2 min) + actual playing (5 min)
- health: player/flag health, starts at 100%, counts down to 0% (= dead)
- profile: preconfigured settings of role in the game
- hit: a blaster receives the ir signal of another blaster
### states
- booting: change profile possible, if confirmed practicing
- practicing: free shooting mode before prestart
- hiding: period with no shooting where players can take position (2 min)
- playing: actual playing (5 min)
- finishing: return to master
### actions (that trigger state change)
- boot: if button is pressed booting, otherwise practicing
- confirm_profile: start of practicing
- prestart: start of hiding
- start: start of playing
- end: start of finishing
### roles
- master
- player
- flag red
- flag green
- flag blue

### rules
- 2 teams
- health counter 100%
- bluetooth triggers prestart
  - countdown to start
  - countdown to end of playing
  - team choice before start
- profiles for the different roles
- flag: health goes down when hit
  if health = 0 -> stop round timer
  
- end of round
  - winner is the team with the highest flag health, or shortest flag timer (flag survived longest)

- offline: shooting in semi-automatic mode


# global round state machine:
States: booting, practicing, hiding, playing, finishing  
Actions: boot, confirm_profile, prestart, start, end
Profiles: master, player, flag red, flag green, flag blue

0. boot
    - if button is pressed during boot, allow changing profile
1. confirm_profile or button is not pressed during boot
    - practicing starts
2. prestart
    - countdown to playing start
    - no shooting
    - no hitting
    - health 100%
3. start
    - countdown to end of game
    - shooting semi-automatic mode
    - getting hit
      - timeout for next hit
      - health -5
      - no shooting possible during timeout
      - timeout 3 seconds (for a round of 5 min)
    - health 0% -> dead -> stop counter
4. end
    - flag health or stopped counter to determine winner
  
Profiles
========
### player
  - screen
```
+---------+--------+
| Health  | Ammo   |
|  100%   | 100%   |
+---------+--------+
|       0:00       |
+------------------+
```
  - health 100%
  - ammo 100%
  - timer: 
    - prestart: countdown to start
    - start: countdown to end
  - hit -> 5 leds on in team color -> out in 3 sec one by one

### flag_red
  - screen
```
+---------+--------+
| Health  |  Red   |
|  100%   |        |
+---------+--------+
|       0:00       |
+------------------+
```
  - health 100%
  - red team color
  - timer: 
    - prestart: countdown to start
    - start: countdown to end
  - hit -> 5 leds on in team colour -> out in 3 sec one by one


### flag_green
  - screen
```
+---------+--------+
| Health  | Green  |
|  100%   |        |
+---------+--------+
|       0:00       |
+------------------+
```
  - health 100%
  - green team color
  - timer: 
    - prestart: countdown to start
    - start: countdown to end
  - hit -> 5 leds on in team colour -> out in 3 sec one by one

### flag blue
  - screen
```
+---------+--------+
| Health  | Blue   |
|  100%   |        |
+---------+--------+
|       0:00       |
+------------------+
```
  - health 100%
  - blue team color
  - timer: 
    - prestart: countdown to start
    - start: countdown to end
  - hit -> 5 leds on in team colour -> out in 3 sec one by one


### master
- prestart: send config via bluetooth
- game modus





# Extra
- 3 teams
- death-match (no teams)
- bluetooth bomb
- bom trigger = touch
   hold to charge + detonate when released
- ammo counter
- statistics who hit who
