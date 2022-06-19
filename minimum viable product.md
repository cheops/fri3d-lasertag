Minimum Viable Product

# vocabulary
- round: 1 cycle of prestart (2 min) + actual round (5 min)
- practice: free shooting mode before prestart
- prestart: 2 min period with no shooting where players can take position
- start: start of actual round (5 min)
- health: player/flag health, starts at 100%, counts down to 0% (= dead)
- profile: preconfigured settings of role in the game
- hit: a blaster receives the ir signal of another blaster


- 2 teams
- health counter 100%
- start round via bluetooth
  - countdown to start
  - countdown to end of round
  - team choice before start
- profiles for the different roles
- flag: health goes down when hit
  if health = 0 -> stop round timer
  
- end of round
  - winner is the team with the highest flag health, or shortest flag timer (flag survived longest)

- offline: shooting in semi-automatic mode


# global round state machine:
0. practice
1. prestart
    - countdown to round start
    - no shooting
    - no hitting
    - health 100%
2. start
    - countdown to end of game
    - shooting semi automatic mode
    - getting hit
      - timeout for next hit
      - health -5
      - no shooting possible during timeout
      - timeout 3 seconds (for a round of 5 min)
    - health 0% -> dead
3. round end
    - flag health and stopped counter to determine winner
  
Profiles
========
## p. player
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
    - start: countdown to round end
  - hit -> 5 leds on in team color -> out in 3 sec one by one

## fr. flag red
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
    - start: countdown to round end
  - hit -> 5 leds on in team colour -> out in 3 sec one by one


## fg. flag green
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
    - start: countdown to round end
  - hit -> 5 leds on in team colour -> out in 3 sec one by one

## fb. flag blue
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
    - start: countdown to round end
  - hit -> 5 leds on in team colour -> out in 3 sec one by one


## m. master
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
