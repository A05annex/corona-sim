import argparse
import json
import random
import time
import matplotlib.pyplot as plt
import numpy as np
import simulate as s
import phases

'''These are the 'phases' the simulation goes through. Phases generally mean a change
in the conditions under which the simulation is running. Often these represent
mandated changes in behaviour of the population in effort to try to affect what
would be the normal path of the simulation.'''

HEALTH_STATES = {
    'well': {'days at state': -1,
             'can be infected': True,
             'next state': 'infected',
             'death rate': 0.0},
    'infected': {'days at state': 2,
                 'can be infected': False,
                 'next state': 'contagious',
                 'death rate': 0.0},
    'contagious': {'days at state': 4,
                   'can be infected': False,
                   'next state': 'recovering',
                   'death rate': 0.03},
    'recovering': {'days at state': 10,
                   'can be infected': False,
                   'next state': 'immune',
                   'death rate': 0.0},
    'immune': {'days at state': -1,
               'can be infected': False,
               'next state': 'well',
               'death rate': 0.0},
    'dead': {'days at state': -1,
             'can be infected': False}
}


def get_mean_infectious_days():
    return HEALTH_STATES['contagious']['days at state']


def set_default_health_state(person):
    person['state'] = 'well'
    person['days'] = 1
    return


def set_initial_infected_state(person):
    person['state'] = 'contagious'
    return


def evaluate_health_for_day(sim_state, person):
    old_health_state = HEALTH_STATES[person['state']]
    person['days'] += 1
    if 0 < old_health_state['days at state'] < person['days']:
        # The person is in a state that progresses after some number of days
        # and that number of days was reached - move to the next state and
        # reset this to the first day at that new state.
        advance_health_state(sim_state, person, old_health_state)

    return


def advance_health_state(sim_state, person, old_health_state):
    # The person is in a state that progresses after some number of days
    # and that number of days was reached - move to the next state and
    # reset this to the first day at that new state.
    if old_health_state['death rate'] > 0.0 and \
            random.random() < old_health_state['death rate']:
        sim_state[s.PEOPLE].remove(person)
        sim_state[s.DAILY_DEATHS] += 1
        sim_state[s.DAILY_POPULATION] -= 1
    else:
        person['state'] = old_health_state['next state']
        person['days'] = 1
        if person['state'] == 'immune':
            # This person was sick long enough to recover (they went
            # from recovery to immune) record them as a recovery.
            sim_state[s.DAILY_RECOVERIES] += 1
        elif person['state'] == 'infected':
            sim_state[s.DAILY_CASES] += 1


def evaluate_contacts(sim_state, person, population):
    population_ct = len(population)
    if HEALTH_STATES[person['state']]['can be infected']:
        # look for contacts with infectious individuals
        for _ in range(int(sim_state[s.CURRENT_DAILY_CONTACTS] / 2)):
            contact = population[random.randint(0, sim_state[s.DAILY_POPULATION] - 1)]
            if contact['state'] == 'contagious':
                # Oh, this the contact between a healthy person who
                # can be infected and a 'contagious' person.
                if random.random() < sim_state[s.CURRENT_TRANSMISSION_PROBABILITY]:
                    # Bummer, this is an infection contact
                    advance_health_state(sim_state, person, HEALTH_STATES[person['state']])
                    # and break because this person is now infected
                    # and can only be infected once
                    break

    elif person['state'] == 'contagious':
        # look for contacts with people who could be infected.
        for _ in range(int(sim_state[s.CURRENT_DAILY_CONTACTS] / 2)):
            contact = population[random.randint(0, sim_state[s.DAILY_POPULATION] - 1)]
            if HEALTH_STATES[contact['state']]['can be infected']:
                # Oh, this the contact between 'contagious' person
                # and a healthy person who can be infected.
                if random.random() < sim_state[s.CURRENT_TRANSMISSION_PROBABILITY]:
                    # Bummer, this is an infection contact
                    advance_health_state(sim_state, contact, HEALTH_STATES[contact['state']])


# ----------------------------------------------------------------------------------------------------------------------
# OK, this is the real start of the simulation
# ----------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description='Run s simulation of in infectious disease spreading through a population.')
parser.add_argument(
    '-ph', '--phases', dest='phases', type=str, default=None,
    help='The JSON file containing the simulation phases description.')
parser.add_argument(
    '-p', '--population', dest='population', type=int, default=s.DEFAULT_POPULATION,
    help='The population for the simulation.')
parser.add_argument(
    '-d', '--days', dest='sim_days', type=int, default=s.DEFAULT_SIMULATION_DAYS,
    help='The length of the simulation in days.')
parser.add_argument(
    '-i', '--infection', dest='infection', type=int, default=s.DEFAULT_INITIAL_INFECTION,
    help='The default infection (not tested).')
args = parser.parse_args()

print('---------------------------------------------------------')
print('---    INFECTIOUS DISEASE SIMULATION CONFIGURATION    ---')
print('---------------------------------------------------------')
print(f'population:               {args.population}')
print(f'simulation length (days): {args.sim_days}')
print(f'initial infection:        {args.infection}')
print(f'phases file:              {args.phases}')
print('---------------------------------------------------------')

if args.phases is not None:
    phases.read_from_file(args.phases)

sim_state = s.create_initial_state(
    HEALTH_STATES, set_default_health_state,
    set_initial_infected_state, evaluate_health_for_day,
    evaluate_contacts, None,
    phases.SIMULATION_PHASES, phases.daily_phase_evaluation,
    population=args.population, simulation_days=args.sim_days,
    initial_infection=args.infection
)
sim_state[s.CURRENT_CONTAGIOUS_DAYS] = get_mean_infectious_days()
phases.set_initial_phase(sim_state)

random.seed(42)
# Everything is setup, get the start time for the simulation
start = time.time()
# OK, let's setup and run the simulation for SIMULATION_DAYS days. The first thing
# we need is the population. For this initial model we will represent each person
# with a dictionary and we will keep their 'state' as one of the health states, and
# 'days' as the number of days they have been at that state. Create a healthy
# population:
for person_id in range(sim_state[s.POPULATION]):
    person = {'id': person_id}
    set_default_health_state(person)
    sim_state[s.PEOPLE].append(person)

# OK, now I've got a healthy population - let's infect the 'INITIAL_INFECTION',
# randomly - these may be people who came from an infected area to their second house,
# or went to a place that was infected to shop or work, and then came back into the
# population we are modeling.
for _ in range(sim_state[s.INITIAL_INFECTION]):
    set_initial_infected_state(
        sim_state[s.PEOPLE][random.randint(0, sim_state[s.POPULATION] - 1)])

# OK, let's simulate. For each day every person will have DAILY_CONTACTS random
# contacts. If it is a contact between a person who can get infected and an
# infected person, then we will guess whether the person was infected based on
# the TRANSMISSION_POSSIBILITY
sim_state[s.DAILY_POPULATION] = sim_state[s.POPULATION]

for day in range(sim_state[s.SIMULATION_DAYS]):
    # Does the simulation state change today based on the
    # numbers at the beginning of the day??
    sim_state[s.DAILY_PHASE_EVALUATION](sim_state, day)
    # initialize statistics for today
    sim_state[s.DAILY_CASES] = 0
    sim_state[s.DAILY_DEATHS] = 0
    sim_state[s.DAILY_RECOVERIES] = 0
    for person in reversed(sim_state[s.PEOPLE]):
        evaluate_health_for_day(sim_state, person)

    for person in sim_state[s.PEOPLE]:
        # can this person infect, or be infected - if so, daily contacts
        # must be traced to see if there is an infection event
        evaluate_contacts(sim_state, person, sim_state[s.PEOPLE])

    # append the today's statistics to the lists
    new_confirmed_cases = sim_state[s.CURRENT_TESTING_PROBABILITY] * sim_state[s.DAILY_CASES]
    new_confirmed_recoveries = sim_state[s.CURRENT_TESTING_PROBABILITY] * sim_state[s.DAILY_RECOVERIES]
    sim_state[s.CUMULATIVE_CASES_SERIES].append(sim_state[s.CUMULATIVE_CASES_SERIES][day] + sim_state[s.DAILY_CASES])
    sim_state[s.CUMULATIVE_CONFIRMED_CASES_SERIES].append(
        sim_state[s.CUMULATIVE_CONFIRMED_CASES_SERIES][day] + new_confirmed_cases)

    sim_state[s.ACTIVE_CASES_SERIES].append(
        sim_state[s.ACTIVE_CASES_SERIES][day] + sim_state[s.DAILY_CASES] - sim_state[s.DAILY_RECOVERIES] - sim_state[
            s.DAILY_DEATHS])
    if sim_state[s.ACTIVE_CASES_SERIES][day + 1] > sim_state[s.ACTIVE_CASES_SERIES][sim_state[s.MAX_ACTIVE_CASES]]:
        sim_state[s.MAX_ACTIVE_CASES] = day + 1
    sim_state[s.ACTIVE_CONFIRMED_CASES_SERIES].append(
        sim_state[s.ACTIVE_CONFIRMED_CASES_SERIES][day] + new_confirmed_cases - new_confirmed_recoveries - sim_state[
            s.DAILY_DEATHS])
    if sim_state[s.ACTIVE_CONFIRMED_CASES_SERIES][day + 1] > \
            sim_state[s.ACTIVE_CONFIRMED_CASES_SERIES][sim_state[s.MAX_ACTIVE_CONFIRMED_CASES]]:
        sim_state[s.MAX_ACTIVE_CONFIRMED_CASES] = day + 1

    sim_state[s.CUMULATIVE_RECOVERIES_SERIES].append(
        sim_state[s.CUMULATIVE_RECOVERIES_SERIES][day] + sim_state[s.DAILY_RECOVERIES])
    sim_state[s.CUMULATIVE_DEATHS_SERIES].append(sim_state[s.CUMULATIVE_DEATHS_SERIES][day] + sim_state[s.DAILY_DEATHS])

    sim_state[s.NEW_CASES_SERIES].append(sim_state[s.DAILY_CASES])
    if sim_state[s.NEW_CASES_SERIES][day + 1] > sim_state[s.NEW_CASES_SERIES][sim_state[s.MAX_NEW_DAILY_CASES]]:
        sim_state[s.MAX_NEW_DAILY_CASES] = day + 1
    sim_state[s.NEW_CONFIRMED_CASES_SERIES].append(new_confirmed_cases)
    if sim_state[s.NEW_CONFIRMED_CASES_SERIES][day + 1] > \
            sim_state[s.NEW_CONFIRMED_CASES_SERIES][sim_state[s.MAX_NEW_DAILY_CONFIRMED_CASES]]:
        sim_state[s.MAX_NEW_DAILY_CONFIRMED_CASES] = day + 1

    sim_state[s.NEW_ACTIVE_CASES_SERIES].append(
        sim_state[s.DAILY_CASES] - sim_state[s.DAILY_RECOVERIES] - sim_state[s.DAILY_DEATHS])
    sim_state[s.NEW_CONFIRMED_ACTIVE_CASES_SERIES].append(
        new_confirmed_cases - new_confirmed_recoveries - sim_state[s.DAILY_DEATHS])
    sim_state[s.NEW_RECOVERIES_SERIES].append(sim_state[s.DAILY_RECOVERIES])
    sim_state[s.NEW_DEATHS_SERIES].append(sim_state[s.DAILY_DEATHS])

# print the results of the simulation
phase_desc = ''
print(f'Simulation Summary:')
print(f'  Setup:')
print(f'    Simulation Days:           {sim_state[s.SIMULATION_DAYS]:16,}')
print(f'    Population:                {sim_state[s.POPULATION]:16,}')
print(f'    Initial Infection:         {sim_state[s.INITIAL_INFECTION]:16,}')
print(f'    Days Contagious:           {HEALTH_STATES["contagious"]["days at state"]:16,}')
print(f'    Phases:')
for key, value in phases.SIMULATION_PHASES.items():
    if 'start day' in value:
        print(f'      {key}:')
        print(f'        start day:               {value["start day"]:14,}')
        print(f'        contacts per day:        {value["daily contacts"]:14,}')
        print(f'        transmission probability:{value["transmission probability"]:14.4f}')
        print(f'        Ro:                      {value["Ro"]:14.4f}')
        if phase_desc != '':
            phase_desc += ', '
        phase_desc += f'{key} Ro={value["Ro"]:.2f}'
print(f'  Daily:')
print(f'    Max Daily New Cases:')
print(f'      On Day:                  {sim_state[s.MAX_NEW_DAILY_CASES]:16,}')
print(f'      Number of New Cases:     {sim_state[s.NEW_CASES_SERIES][sim_state[s.MAX_NEW_DAILY_CASES]]:16,}')
print(f'      Cumulative Cases:        {sim_state[s.CUMULATIVE_CASES_SERIES][sim_state[s.MAX_NEW_DAILY_CASES]]:16,}'
      f'({sim_state[s.CUMULATIVE_CASES_SERIES][sim_state[s.MAX_NEW_DAILY_CASES]] * 100.0 / sim_state[s.POPULATION]:5.2f}%)')
print(f'    Maximum Active Cases:')
print(f'      On Day:                  {sim_state[s.MAX_ACTIVE_CASES]:16,}')
print(f'      Number of Active Cases:  {sim_state[s.ACTIVE_CASES_SERIES][sim_state[s.MAX_ACTIVE_CASES]]:16,}')
print(f'      Cumulative Cases:        {sim_state[s.CUMULATIVE_CASES_SERIES][sim_state[s.MAX_ACTIVE_CASES]]:16,}'
      f'({sim_state[s.CUMULATIVE_CASES_SERIES][sim_state[s.MAX_ACTIVE_CASES]] * 100.0 / sim_state[s.POPULATION]:5.2f}%)')
print(f'  Cumulative:')
print(f'    Cumulative Cases:          {sim_state[s.CUMULATIVE_CASES_SERIES][sim_state[s.SIMULATION_DAYS]]:16,}'
      f'({sim_state[s.CUMULATIVE_CASES_SERIES][sim_state[s.SIMULATION_DAYS]] * 100.0 / sim_state[s.POPULATION]:5.2f}%)')
print(f'    Cumulative Recoveries:     {sim_state[s.CUMULATIVE_RECOVERIES_SERIES][sim_state[s.SIMULATION_DAYS]]:16,}'
      f'({sim_state[s.CUMULATIVE_RECOVERIES_SERIES][sim_state[s.SIMULATION_DAYS]] * 100.0 / sim_state[s.POPULATION]:5.2f}%)')
print(f'    Cumulative Deaths:         {sim_state[s.CUMULATIVE_DEATHS_SERIES][sim_state[s.SIMULATION_DAYS]]:16,}'
      f'({sim_state[s.CUMULATIVE_DEATHS_SERIES][sim_state[s.SIMULATION_DAYS]] * 100.0 / sim_state[s.POPULATION]:5.2f}%)')

print(f'\nSimulation time: {time.time() - start:.4f}sec\n')

# save the data from this simulation to a file
phases_data = {}
for key, value in phases.SIMULATION_PHASES.items():
    if 'start day' in value:
        phases_data[key] = {
            'start_day': value['start day'],
            'daily_contacts': value['daily contacts'],
            'transmission_probability': value['transmission probability'],
            'Ro': value["Ro"]
        }

data = {'simulation_days': sim_state[s.SIMULATION_DAYS],
        'population': sim_state[s.POPULATION],
        'initial_infection': sim_state[s.INITIAL_INFECTION],
        'days_contagious': HEALTH_STATES['contagious']['days at state'],
        'phases': phases_data,
        'max_new_daily_cases_day': sim_state[s.MAX_NEW_DAILY_CASES],
        'max_active_cases_day': sim_state[s.MAX_ACTIVE_CASES],
        'cumulative_cases': sim_state[s.CUMULATIVE_CASES_SERIES][-1],
        'cumulative_recoveries': sim_state[s.CUMULATIVE_RECOVERIES_SERIES][-1],
        'cumulative_deaths': sim_state[s.CUMULATIVE_DEATHS_SERIES][-1],
        'cumulative_cases_series': sim_state[s.CUMULATIVE_CASES_SERIES],
        'active_cases_series': sim_state[s.ACTIVE_CASES_SERIES],
        'cumulative_recoveries_series': sim_state[s.CUMULATIVE_RECOVERIES_SERIES],
        'cumulative_deaths_series': sim_state[s.CUMULATIVE_DEATHS_SERIES],
        'daily_new_cases_series': sim_state[s.NEW_CASES_SERIES],
        'daily_new_active_cases_series': sim_state[s.NEW_ACTIVE_CASES_SERIES],
        'daily_new_recoveries_series': sim_state[s.NEW_RECOVERIES_SERIES],
        'daily_new_deaths_series': sim_state[s.NEW_DEATHS_SERIES]}
with open("./data/expl3/test_x.json", "w") as fw:
    json.dump(data, fw, indent=2)

# plot the results
# These are the cumulative stats
plt.clf()
plt.title(
    f'Total Cases Simulation, {sim_state[s.POPULATION]} population,\n '
    f'{phase_desc}')
plt.xlabel('days')
plt.ylabel('cumulative number')
plt.xticks(np.arange(0, 211, 14))
plt.grid(b=True, which='major', color='#aaaaff', linestyle='-')
for key, phase in phases.SIMULATION_PHASES.items():
    start_day = phase.get('start day', 0)
    if start_day > 1:
        plt.scatter([start_day, start_day, start_day, start_day, start_day, start_day],
                    [sim_state[s.CUMULATIVE_CASES_SERIES][start_day],
                     sim_state[s.CUMULATIVE_CONFIRMED_CASES_SERIES][start_day],
                     sim_state[s.ACTIVE_CASES_SERIES][start_day],
                     sim_state[s.ACTIVE_CONFIRMED_CASES_SERIES][start_day],
                     sim_state[s.CUMULATIVE_RECOVERIES_SERIES][start_day],
                     sim_state[s.CUMULATIVE_DEATHS_SERIES][start_day]],
                    label=key)

plt.plot(sim_state[s.CUMULATIVE_CASES_SERIES], label='cumulative cases')
plt.plot(sim_state[s.CUMULATIVE_CONFIRMED_CASES_SERIES], label='cumulative confirmed cases')
plt.plot(sim_state[s.ACTIVE_CASES_SERIES], label='active cases')
plt.plot(sim_state[s.ACTIVE_CONFIRMED_CASES_SERIES], label='active confirmed cases')
plt.plot(sim_state[s.CUMULATIVE_RECOVERIES_SERIES], label='recoveries')
plt.plot(sim_state[s.CUMULATIVE_DEATHS_SERIES], label='deaths')
plt.legend()
plt.show()
plt.pause(0.1)

# These are the daily stats
plt.clf()
plt.title(
    f'Daily Cases Simulation, {sim_state[s.POPULATION]} population,\n '
    f'{phase_desc}')
plt.xlabel('days')
plt.ylabel('daily number')
plt.xticks(np.arange(0, 211, 14))
plt.grid(b=True, which='major', color='#aaaaff', linestyle='-')
for key, phase in phases.SIMULATION_PHASES.items():
    start_day = phase.get('start day', 0)
    if start_day > 1:
        plt.scatter([start_day, start_day, start_day, start_day, start_day, start_day],
                    [sim_state[s.NEW_CASES_SERIES][start_day],
                     sim_state[s.NEW_CONFIRMED_CASES_SERIES][start_day],
                     sim_state[s.NEW_ACTIVE_CASES_SERIES][start_day],
                     sim_state[s.NEW_CONFIRMED_ACTIVE_CASES_SERIES][start_day],
                     sim_state[s.NEW_RECOVERIES_SERIES][start_day],
                     sim_state[s.NEW_DEATHS_SERIES][start_day]],
                    label=key)
plt.plot(sim_state[s.NEW_CASES_SERIES], label='daily new cases')
plt.plot(sim_state[s.NEW_CONFIRMED_CASES_SERIES], label='daily new confirmed cases')
plt.plot(sim_state[s.NEW_ACTIVE_CASES_SERIES], label='daily active cases')
plt.plot(sim_state[s.NEW_CONFIRMED_ACTIVE_CASES_SERIES], label='new active confirmed cases')
plt.plot(sim_state[s.NEW_RECOVERIES_SERIES], label='daily recoveries')
plt.plot(sim_state[s.NEW_DEATHS_SERIES], label='daily deaths')
plt.legend()
plt.show()
plt.pause(0.1)
