Minimum Viable Product

# vocabulary
- round: 1 cycle of practicing (2 min) + actual playing (5 min)
- health: player/flag health, starts at 100%, counts down to 0% (= dead)
- profile: preconfigured settings of role in the game
- hit: a blaster receives the ir signal of another blaster
- Red, Green, Blue = Rex, Giggle, Buzz
### states
- booting: change profile possible, if confirmed practicing
- practicing: free shooting mode before prestart
- hiding: period with no shooting where players can take position (2 min)
- playing: actual playing (5 min)
- finishing: return to master
### events (that trigger state change)
- boot: if button is pressed booting, otherwise practicing
- confirm_profile: start of practicing
- prestart: start of hiding
- countdown-end: the hiding or playing time is finished
- dead: health <= 0
### roles
- master
- player
- flag rex
- flag giggle
- flag buzz
### inputs
- shoot
- hit
- countdown-end
- button
- touch-left
- touch-middle
- touch-right


### rules
- 3 teams (Rex, Giggle, Buzz)
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
Profiles: master, player, flag rex, flag giggle, flag buzz

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
|    countdown     |
|       0:00       |
+------------------+
|    player buzz   |
+------------------+
```
  - health 100%
  - ammo 100%
  - timer: 
    - prestart: countdown to start
    - start: countdown to end
  - hit -> 5 leds on in team color -> out in 3 sec one by one

### flag_rex
  - screen
```
+---------+--------+
| Health  |  Rex   |
|  100%   |        |
+---------+--------+
|    countdown     |
|       0:00       |
+------------------+
|     flag rex     |
+------------------+
```
  - health 100%
  - red team color = rex
  - timer: 
    - prestart: countdown to start
    - start: countdown to end
  - hit -> 5 leds on in team colour -> out in 3 sec one by one


### flag_giggle
  - screen
```
+---------+--------+
| Health  | Giggle |
|  100%   |        |
+---------+--------+
|    countdown     |
|       0:00       |
+------------------+
|    flag giggle   |
+------------------+
```
  - health 100%
  - green team color = giggle
  - timer: 
    - prestart: countdown to start
    - start: countdown to end
  - hit -> 5 leds on in team colour -> out in 3 sec one by one

### flag buzz
  - screen
```
+---------+--------+
| Health  | Buzz   |
|  100%   |        |
+---------+--------+
|    countdown     |
|       0:00       |
+------------------+
|     flag buzz    |
+------------------+
```
  - health 100%
  - blue team color = buzz
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
