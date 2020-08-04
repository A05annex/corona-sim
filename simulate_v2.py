"""
The code that holds the state of the simulation, runs the simulation, saves the simulation to a file,
reads a simulation from a file, and plots a simulation.
"""
import json
import random
import sys
import matplotlib.pyplot as plt
import numpy as np

# larger simulation defaults
DEFAULT_POPULATION = 50000
DEFAULT_INITIAL_INFECTION = 20
DEFAULT_SIMULATION_DAYS = 211

# define the keys for the simulation state
# some of the basic stuff
SIMULATION_DAYS = 'simulation_days'
POPULATION = 'population'
INITIAL_INFECTION = 'initial_infection'
PEOPLE = 'people'
HOSPITALIZED_PEOPLE = 'hospitalized_people'
HEALTH_STATES = 'health_states'
PHASES = 'phases'
DAILY_PHASE_EVALUATION = 'daily_phase_evaluation'
SET_DEFAULT_HEALTH = 'set_initial_health'
SET_INFECTED = 'set_infected'
DAILY_HEALTH_EVALUATION = 'daily_health_evaluation'
DAILY_EVALUATE_CONTACTS = 'daily_evaluate_contacts'
DAILY_UPDATE_STATE = 'daily_update_state'
UPDATE_TESTING_RATES = 'update_testing_rates'
EVENTS = 'events'
DAILY_EVENT_EVALUATION = 'daily_event_evaluation'

# Properties for the simulation of the current phase, note that everything
# comes from the phases except current contagious days which comes from state
CURRENT_PHASE = 'current_phase'
HAS_NEXT_PHASE = 'has_next_phase'
CURRENT_DAILY_CONTACTS = 'current_daily_contacts'
CURRENT_CONTAGIOUS_DAYS = 'current_contagious_days'
CURRENT_TRANSMISSION_PROBABILITY = 'current_transmission_probability'
CURRENT_TESTING_PROBABILITY = 'current_testing_probability'
NORMAL_DAILY_CONTACTS = 'normal_daily_contacts'
NORMAL_TRANSMISSION_PROBABILITY = 'normal_transmission_probability'

# State for the current day.
DAILY_POPULATION = 'today_population'
DAILY_CASES = 'today_cases'
DAILY_CONFIRMED_CASES = 'today_confirmed_cases'
DAILY_RECOVERIES = 'today_recoveries'
DAILY_CONFIRMED_RECOVERIES = 'today_confirmed_recoveries'
DAILY_DEATHS = 'today_deaths'
DAILY_CONFIRMED_DEATHS = 'today_confirmed_deaths'
DAILY_HOSPITALIZATIONS = 'today_hospitalizations'
DAILY_ICU = 'today_ICU'

# There are days when the maximum of something happens.
MAX_NEW_DAILY_CASES = 'max_new_daily_cases_day'
MAX_NEW_DAILY_CONFIRMED_CASES = 'max_new_daily_confirmed_cases_day'
MAX_ACTIVE_CASES = 'max_active_cases_day'
MAX_ACTIVE_CONFIRMED_CASES = 'max_active_confirmed_cases_day'
MAX_ACTIVE_HOSPITALIZATIONS = 'max_active_hospitalizations_day'
MAX_ACTIVE_ICU = 'max_active_ICU_day'

# The series data being generated by the simulation - the keys for these series are appropriate labels
# for the series when they are graphed.
CUMULATIVE_CASES_SERIES = 'cumulative cases'
CUMULATIVE_CONFIRMED_CASES_SERIES = 'cumulative confirmed cases'
CUMULATIVE_RECOVERIES_SERIES = 'cumulative recoveries'
CUMULATIVE_CONFIRMED_RECOVERIES_SERIES = 'cumulative confirmed recoveries'
CUMULATIVE_DEATHS_SERIES = 'cumulative confirmed deaths'
CUMULATIVE_CONFIRMED_DEATHS_SERIES = 'cumulative deaths'
ACTIVE_CASES_SERIES = 'active cases'
ACTIVE_CONFIRMED_CASES_SERIES = 'active confirmed cases'
ACTIVE_HOSPITALIZED_CASES_SERIES = 'active hospitalized cases'
ACTIVE_ICU_CASES_SERIES = 'active ICU cases'
NEW_CASES_SERIES = 'new cases'
NEW_CONFIRMED_CASES_SERIES = 'new confirmed cases'
NEW_ACTIVE_CASES_SERIES = 'new active cases'
NEW_CONFIRMED_ACTIVE_CASES_SERIES = 'new confirmed active cases'
NEW_RECOVERIES_SERIES = 'new recoveries'
NEW_DEATHS_SERIES = 'new deaths'

# The keys that should be serialized to a file to save the results of a simulation.
_SERIALIZE_KEYS = [
    SIMULATION_DAYS, POPULATION, INITIAL_INFECTION, MAX_NEW_DAILY_CASES, MAX_ACTIVE_CASES,
    MAX_ACTIVE_HOSPITALIZATIONS, MAX_ACTIVE_ICU, CUMULATIVE_CASES_SERIES,
    CUMULATIVE_CONFIRMED_CASES_SERIES, CUMULATIVE_RECOVERIES_SERIES,
    CUMULATIVE_CONFIRMED_RECOVERIES_SERIES, CUMULATIVE_DEATHS_SERIES,
    CUMULATIVE_CONFIRMED_DEATHS_SERIES, ACTIVE_CASES_SERIES,
    ACTIVE_CONFIRMED_CASES_SERIES, ACTIVE_HOSPITALIZED_CASES_SERIES, ACTIVE_ICU_CASES_SERIES,
    NEW_CASES_SERIES, NEW_CONFIRMED_CASES_SERIES, NEW_ACTIVE_CASES_SERIES,
    NEW_CONFIRMED_ACTIVE_CASES_SERIES, NEW_RECOVERIES_SERIES, NEW_DEATHS_SERIES
]


def create_initial_state(health_states, set_default_health_state,
                         set_initial_infected_state, daily_health_evaluation,
                         evaluate_contacts, update_testing_rates,
                         daily_update_state,
                         phases, daily_phase_evaluation,
                         events=None, daily_event_evaluation=None,
                         simulation_days=DEFAULT_SIMULATION_DAYS,
                         population=DEFAULT_POPULATION,
                         initial_infection=DEFAULT_INITIAL_INFECTION):
    """

    :param health_states:
    :param set_default_health_state:
    :param set_initial_infected_state:
    :param daily_health_evaluation:
    :param evaluate_contacts:
    :param update_testing_rates:
    :param daily_update_state:
    :param phases:
    :param daily_phase_evaluation:
    :param events:
    :param daily_event_evaluation:
    :param simulation_days:
    :param population:
    :param initial_infection:
    :return: (dict) The initialized simulation state.
    """
    sim_state = {
        SIMULATION_DAYS: simulation_days,
        POPULATION: population,
        INITIAL_INFECTION: initial_infection,
        PEOPLE: [],
        HOSPITALIZED_PEOPLE: [],
        HEALTH_STATES: health_states,
        SET_DEFAULT_HEALTH: set_default_health_state,
        SET_INFECTED: set_initial_infected_state,
        DAILY_HEALTH_EVALUATION: daily_health_evaluation,
        DAILY_EVALUATE_CONTACTS: evaluate_contacts,
        DAILY_UPDATE_STATE: daily_update_state,
        DAILY_HOSPITALIZATIONS: 0,
        DAILY_DEATHS: 0,
        UPDATE_TESTING_RATES: update_testing_rates,
        PHASES: phases,
        DAILY_PHASE_EVALUATION: daily_phase_evaluation,
        EVENTS: events,
        DAILY_EVENT_EVALUATION: daily_event_evaluation,
        MAX_NEW_DAILY_CASES: 0,
        MAX_NEW_DAILY_CONFIRMED_CASES: 0,
        MAX_ACTIVE_CASES: 0,
        MAX_ACTIVE_CONFIRMED_CASES: 0,
        MAX_ACTIVE_HOSPITALIZATIONS: 0,
        MAX_ACTIVE_ICU: 0,
        CUMULATIVE_CASES_SERIES: [],
        CUMULATIVE_CONFIRMED_CASES_SERIES: [],
        CUMULATIVE_RECOVERIES_SERIES: [],
        CUMULATIVE_CONFIRMED_RECOVERIES_SERIES: [],
        CUMULATIVE_DEATHS_SERIES: [],
        CUMULATIVE_CONFIRMED_DEATHS_SERIES: [],
        ACTIVE_CASES_SERIES: [],
        ACTIVE_CONFIRMED_CASES_SERIES: [],
        ACTIVE_HOSPITALIZED_CASES_SERIES: [],
        ACTIVE_ICU_CASES_SERIES: [],
        NEW_CASES_SERIES: [],
        NEW_CONFIRMED_CASES_SERIES: [],
        NEW_ACTIVE_CASES_SERIES: [],
        NEW_CONFIRMED_ACTIVE_CASES_SERIES: [],
        NEW_RECOVERIES_SERIES: [],
        NEW_DEATHS_SERIES: []
    }
    return sim_state


def run_simulation(ss):
    """
    Run the simulation

    :param ss: (dict, required) The simulation state.
    :return: None
    """
    # OK, let's setup and run the simulation for SIMULATION_DAYS days. The first thing
    # we need is the population. For this initial model we will represent each person
    # with a dictionary and we will keep their 'state' as one of the health states, and
    # 'days' as the number of days they have been at that state. Create a healthy
    # population:
    for person_id in range(ss[POPULATION]):
        person = {'id': person_id}
        ss[SET_DEFAULT_HEALTH](person, True)
        ss[PEOPLE].append(person)

    # OK, let's simulate. For each day every person will have DAILY_CONTACTS random
    # contacts. If it is a contact between a person who can get infected and an
    # infected person, then we will guess whether the person was infected based on
    # the TRANSMISSION_POSSIBILITY
    ss[DAILY_POPULATION] = ss[POPULATION]
    for day in range(-1,ss[SIMULATION_DAYS]):
        # initialize statistics for today
        ss[DAILY_CASES] = 0
        ss[DAILY_CONFIRMED_CASES] = 0
        ss[DAILY_RECOVERIES] = 0
        ss[DAILY_CONFIRMED_RECOVERIES] = 0
        ss[DAILY_DEATHS] = 0
        ss[DAILY_CONFIRMED_DEATHS] = 0
        ss[DAILY_HOSPITALIZATIONS] = 0
        ss[DAILY_ICU] = 0
        # update the health state of every person
        if day == -1:
            # OK, now I've got a healthy population - let's infect the 'INITIAL_INFECTION',
            # randomly - these may be people who came from an infected area to their second house,
            # or went to a place that was infected to shop or work, and then came back into the
            # population we are modeling.
            while ss[INITIAL_INFECTION] > ss[DAILY_CONFIRMED_CASES]:
                ss[SET_INFECTED](
                    ss, ss[PEOPLE][random.randint(0, ss[POPULATION] - 1)])

            ss[CUMULATIVE_CASES_SERIES].append(ss[DAILY_CASES])
            ss[CUMULATIVE_CONFIRMED_CASES_SERIES].append(ss[DAILY_CONFIRMED_CASES])

            ss[ACTIVE_CASES_SERIES].append(ss[DAILY_CASES] - ss[DAILY_RECOVERIES] - ss[DAILY_DEATHS])
            ss[ACTIVE_CONFIRMED_CASES_SERIES].append(
                ss[DAILY_CONFIRMED_CASES] - ss[DAILY_CONFIRMED_RECOVERIES] - ss[DAILY_CONFIRMED_DEATHS])
            ss[ACTIVE_HOSPITALIZED_CASES_SERIES].append(ss[DAILY_HOSPITALIZATIONS])
            ss[ACTIVE_ICU_CASES_SERIES].append(ss[DAILY_ICU])
            ss[CUMULATIVE_RECOVERIES_SERIES].append(ss[DAILY_RECOVERIES])
            ss[CUMULATIVE_CONFIRMED_RECOVERIES_SERIES].append(ss[DAILY_CONFIRMED_RECOVERIES])
            ss[CUMULATIVE_DEATHS_SERIES].append(ss[DAILY_DEATHS])
            ss[CUMULATIVE_CONFIRMED_DEATHS_SERIES].append(ss[DAILY_CONFIRMED_DEATHS])

            ss[NEW_CASES_SERIES].append(ss[DAILY_CASES])
            ss[NEW_CONFIRMED_CASES_SERIES].append(ss[DAILY_CONFIRMED_CASES])
            ss[NEW_ACTIVE_CASES_SERIES].append(
                ss[DAILY_CASES] - ss[DAILY_RECOVERIES] - ss[DAILY_DEATHS])
            ss[NEW_CONFIRMED_ACTIVE_CASES_SERIES].append(
                ss[DAILY_CONFIRMED_CASES] - ss[DAILY_CONFIRMED_RECOVERIES] - ss[DAILY_DEATHS])
            ss[NEW_RECOVERIES_SERIES].append(ss[DAILY_RECOVERIES])
            ss[NEW_DEATHS_SERIES].append(ss[DAILY_DEATHS])

        else:
            sys.stdout.write(f' evaluate day {day}: population {ss[DAILY_POPULATION]};'
                             f' new {ss[NEW_CONFIRMED_CASES_SERIES][day]};'
                             f' cumulative {ss[CUMULATIVE_CONFIRMED_CASES_SERIES][day]};'
                             f' deaths {ss[CUMULATIVE_CONFIRMED_DEATHS_SERIES][day]}                \r')
            sys.stdout.flush()

            # Does the description of the health states change today based on the
            # numbers at the beginning of the day??
            ss[DAILY_UPDATE_STATE](ss, day)
            # Does the simulation phase change today based on the
            # numbers at the beginning of the day??
            if ss[DAILY_PHASE_EVALUATION](ss, day):
                ss[UPDATE_TESTING_RATES](ss[CURRENT_TESTING_PROBABILITY])

            for person in reversed(ss[HOSPITALIZED_PEOPLE]):
                ss[DAILY_HEALTH_EVALUATION](ss, person)
            for person in reversed(ss[PEOPLE]):
                ss[DAILY_HEALTH_EVALUATION](ss, person)

            for person in ss[PEOPLE]:
                # can this person infect, or be infected - if so, daily contacts
                # must be traced to see if there is an infection event
                ss[DAILY_EVALUATE_CONTACTS](ss, person, ss[PEOPLE])

            if ss[DAILY_EVENT_EVALUATION] is not None:
                ss[DAILY_EVENT_EVALUATION](ss, day)

            # append the today's statistics to the lists
            # new_confirmed_cases = sim_state[s.CURRENT_TESTING_PROBABILITY] * sim_state[s.DAILY_CASES]
            # new_confirmed_recoveries = sim_state[s.CURRENT_TESTING_PROBABILITY] * sim_state[s.DAILY_RECOVERIES]
            ss[CUMULATIVE_CASES_SERIES].append(
                ss[CUMULATIVE_CASES_SERIES][day] + ss[DAILY_CASES])
            ss[CUMULATIVE_CONFIRMED_CASES_SERIES].append(
                ss[CUMULATIVE_CONFIRMED_CASES_SERIES][day] + ss[DAILY_CONFIRMED_CASES])

            ss[ACTIVE_CASES_SERIES].append(
                ss[ACTIVE_CASES_SERIES][day] + ss[DAILY_CASES]
                - ss[DAILY_RECOVERIES] - ss[DAILY_DEATHS])
            if ss[ACTIVE_CASES_SERIES][day + 1] > ss[ACTIVE_CASES_SERIES][ss[MAX_ACTIVE_CASES]]:
                ss[MAX_ACTIVE_CASES] = day + 1
            ss[ACTIVE_CONFIRMED_CASES_SERIES].append(
                ss[ACTIVE_CONFIRMED_CASES_SERIES][day] + ss[DAILY_CONFIRMED_CASES]
                - ss[DAILY_CONFIRMED_RECOVERIES] - ss[DAILY_CONFIRMED_DEATHS])
            if ss[ACTIVE_CONFIRMED_CASES_SERIES][day + 1] > \
                    ss[ACTIVE_CONFIRMED_CASES_SERIES][ss[MAX_ACTIVE_CONFIRMED_CASES]]:
                ss[MAX_ACTIVE_CONFIRMED_CASES] = day + 1
            ss[ACTIVE_HOSPITALIZED_CASES_SERIES].append(
                ss[ACTIVE_HOSPITALIZED_CASES_SERIES][day] + ss[DAILY_HOSPITALIZATIONS])
            if ss[ACTIVE_HOSPITALIZED_CASES_SERIES][day + 1] > \
                    ss[ACTIVE_HOSPITALIZED_CASES_SERIES][ss[MAX_ACTIVE_HOSPITALIZATIONS]]:
                ss[MAX_ACTIVE_HOSPITALIZATIONS] = day + 1
            ss[ACTIVE_ICU_CASES_SERIES].append(
                ss[ACTIVE_ICU_CASES_SERIES][day] + ss[DAILY_ICU])
            if ss[ACTIVE_ICU_CASES_SERIES][day + 1] > \
                    ss[ACTIVE_ICU_CASES_SERIES][ss[MAX_ACTIVE_ICU]]:
                ss[MAX_ACTIVE_ICU] = day + 1

            ss[CUMULATIVE_RECOVERIES_SERIES].append(
                ss[CUMULATIVE_RECOVERIES_SERIES][day] + ss[DAILY_RECOVERIES])
            ss[CUMULATIVE_CONFIRMED_RECOVERIES_SERIES].append(
                ss[CUMULATIVE_CONFIRMED_RECOVERIES_SERIES][day] + ss[DAILY_CONFIRMED_RECOVERIES])
            ss[CUMULATIVE_DEATHS_SERIES].append(
                ss[CUMULATIVE_DEATHS_SERIES][day] + ss[DAILY_DEATHS])
            ss[CUMULATIVE_CONFIRMED_DEATHS_SERIES].append(
                ss[CUMULATIVE_CONFIRMED_DEATHS_SERIES][day] + ss[DAILY_CONFIRMED_DEATHS])

            ss[NEW_CASES_SERIES].append(ss[DAILY_CASES])
            if ss[NEW_CASES_SERIES][day + 1] > ss[NEW_CASES_SERIES][ss[MAX_NEW_DAILY_CASES]]:
                ss[MAX_NEW_DAILY_CASES] = day + 1
            ss[NEW_CONFIRMED_CASES_SERIES].append(ss[DAILY_CONFIRMED_CASES])
            if ss[NEW_CONFIRMED_CASES_SERIES][day + 1] > \
                    ss[NEW_CONFIRMED_CASES_SERIES][ss[MAX_NEW_DAILY_CONFIRMED_CASES]]:
                ss[MAX_NEW_DAILY_CONFIRMED_CASES] = day + 1

            ss[NEW_ACTIVE_CASES_SERIES].append(
                ss[DAILY_CASES] - ss[DAILY_RECOVERIES] - ss[DAILY_DEATHS])
            ss[NEW_CONFIRMED_ACTIVE_CASES_SERIES].append(
                ss[DAILY_CONFIRMED_CASES] - ss[DAILY_CONFIRMED_RECOVERIES] - ss[DAILY_DEATHS])
            ss[NEW_RECOVERIES_SERIES].append(ss[DAILY_RECOVERIES])
            ss[NEW_DEATHS_SERIES].append(ss[DAILY_DEATHS])


def write_data(ss, file_name):
    # save the data from this simulation to a file
    phases_data = {}
    for key, value in ss[PHASES].items():
        if 'start day' in value:
            phases_data[key] = {
                'start_day': value['start day'],
                'daily_contacts': value['daily contacts'],
                'transmission_probability': value['transmission probability'],
                'Ro': value["Ro"]
            }

    data = {PHASES: phases_data}
    for key in _SERIALIZE_KEYS:
        data[key] = ss[key]

    with open(file_name, "w") as fw:
        json.dump(data, fw, indent=2)


def graph_simulation(ss, title, series):
    """
    Graph a set of series from this simulation

    :param ss: (dict, required) The simulation state.
    :param title: (str, required)
    :param series: ([str,str,...], required) The
    :return:
    """
    # plot the results
    # These are the cumulative stats
    plt.clf()
    plt.title(title)
    plt.xlabel('days')
    plt.ylabel('count')
    tic_spacing = 14 if ss[SIMULATION_DAYS] <= 211 else 28
    plt.xticks(np.arange(0, ss[SIMULATION_DAYS], tic_spacing))
    plt.grid(b=True, which='major', color='#aaaaff', linestyle='-')
    for key, phase in ss[PHASES].items():
        start_day = phase.get('start day', 0)
        if start_day > 1:
            day = []
            data = []
            for series_key in series:
                day.append(start_day)
                data.append(ss[series_key][start_day])
            plt.scatter(day, data, label=f'{key}, Re={phase["Ro"]:.2f}')
    for series_key in series:
        plt.plot(ss[series_key], label=series_key)
    plt.legend()
    plt.show()
    plt.pause(0.1)


def test_condition(ss, condition, day):
    advance = False
    if condition['type'] == 'cumulative cases exceeds':
        advance = ss[CUMULATIVE_CASES_SERIES][day] >= condition['count']
    elif condition['type'] == 'daily new confirmed above':
        advance = ss[NEW_CONFIRMED_CASES_SERIES][day] >= condition['count']
    elif condition['type'] == 'daily new confirmed below':
        advance = ss[NEW_CONFIRMED_CASES_SERIES][day] <= condition['count']
    elif condition['type'] == 'cumulative confirmed cases exceeds':
        advance = ss[CUMULATIVE_CONFIRMED_CASES_SERIES][day] >= condition['count']
    elif condition['type'] == 'days after max active':
        advance = day - ss[MAX_ACTIVE_CASES] > condition['days']
    elif condition['type'] == 'days after confirmed max active':
        advance = day - ss[MAX_ACTIVE_CONFIRMED_CASES] > condition['days']
    elif condition['type'] == 'days in phase':
        advance = day - ss[CURRENT_PHASE]['start day'] > condition['days']
    elif condition['type'] == 'day in simulation':
        advance = day == condition['day']
    else:
        print(f'Unrecognized condition: "{condition["type"]}"')

    return advance
