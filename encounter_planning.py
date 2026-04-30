import random
import os
import math

# clearing the terminal 
os.system('cls' if os.name == 'nt' else 'clear')

# drawing a random number, hoping for even 
print("Let's calculate some simple PF2e encounter outcome likelihoods.")
print("(This fight will be a stand-and-bang)")
print("\n")

print("===PLAYER CHARACTER===")
player_prof = 1
player_hp = 12
player_weapon_die = 10
player_damage_mod = 4
player_is_agile = 0
player_AC = 16

print(f"Player HP: {player_hp}")
print("\n")

print("===ENEMIES===")
num_enemies = 3

enemy_prof = 1
enemy_hp = 4
enemy_weapon_die = 6
enemy_damage_mod = 1
enemy_is_agile = 0
enemy_AC = 11

enemies = []

for i in range(num_enemies): 
    enemies.append({
        "hp": enemy_hp, 
        "prof": enemy_prof, 
        "die": enemy_weapon_die, 
        "mod": enemy_damage_mod, 
        "AC": enemy_AC, 
        "is_agile": enemy_is_agile
    }) 

print(f"Enemies created: {len(enemies)}")
print("\n")

def roll_d20(): 
    return random.randint(1,20)

def roll_damage(die, mod): 
    return random.randint(1,die) + mod

def get_map_penalty(attack_number, is_agile): 
    """
    attack_number: 1, 2, or 3
    is_agile: 0/1 or False/True
    """
    if attack_number == 1: 
        return 0 
    elif attack_number == 2: 
        return -4 if is_agile else -5
    elif attack_number == 3: 
        return -8 if is_agile else -10
    return 0

def resolve_attack(attacker, defender, attack_number): 
    """
    attacker: dict with prof, die, mod, is_agile
    defender: dict with hp, AC
    attack_number: 1, 2, or 3
    """

    attack_roll = roll_d20()
    map_penalty = get_map_penalty(attack_number, attacker["is_agile"])

    total_attack = attack_roll + attacker["prof"] + map_penalty

    print(f"Attack {attack_number}: Roll={attack_roll}, Total Attack={total_attack}")

    if total_attack >= defender["AC"]:
        damage = roll_damage(attacker["die"], attacker["mod"])
        defender["hp"] -= damage
        print(f"Hit! Damage={damage}, Defender HP={defender['hp']}")
    else: 
        print("Miss!")
    
    return defender

def run_encounter(): 
    # === FIRST ROUND OF COMBAT ===
    print("Let's simulate the first round of combat, where the player attacks first.")

    # === PLAYER TURN === 
    print("Player's turn:")
    player = {
        "prof": player_prof, 
        "die": player_weapon_die,
        "mod": player_damage_mod,
        "is_agile": player_is_agile,
        "AC": player_AC
    }

    enemies = []
    for i in range(num_enemies): 
        enemies.append({
            "hp": enemy_hp, 
            "prof": enemy_prof, 
            "die": enemy_weapon_die, 
            "mod": enemy_damage_mod, 
            "AC": enemy_AC, 
            "is_agile": enemy_is_agile
        })

    target = enemies[0]

    for attack in range(1,4): 
        target = resolve_attack(player, target, attack)

        if target["hp"] <= 0: 
            print("Enemy defeated!")
            break

    # === ENEMY TURN ===
    print("\nEnemies' turn:")

    player = {
        "hp": player_hp,
        "AC": player_AC, 
        "prof": player_prof, 
        "die": player_weapon_die, 
        "mod": player_damage_mod, 
        "is_agile": player_is_agile
    }

    for enemy_index, enemy in enumerate(enemies): 
        print(f"\nEnemy {enemy_index + 1} attacks:")

        for attack in range(1,4): 

            player = resolve_attack(enemy, player, attack)

            if player["hp"] <= 0: 
                print("Player defeated!")
                break
            
        if player["hp"] <= 0: 
            break
            

    # === ROUND RESULTS === 
    print("\n===ROUND RESULT===")
    print(f"Player HP: {player['hp']}")

    for i, e in enumerate(enemies): 
        print(f"Enemy {i+1} HP: {e['hp']}")

    player_alive = player["hp"] > 0
    return player_alive

trials = 1000
wins = 0

for i in range(trials): 
    if run_encounter(): 
        wins += 1

print(f"\n === SIMULATION RESULT ===")
print(f"Win rate: {wins / trials:.3f}")
print(f"Loss rate: {(trials - wins) / trials:.3f}")

