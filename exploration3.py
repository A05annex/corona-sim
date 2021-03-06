import expl_tools as tools
import simulate as s

data_dir = './data/expl3/'
test_set = tools.read_run_set(data_dir, 'cov_50000')
event_set = tools.read_run_set(data_dir, 'cov_50000_e70')

title_template = '{} Simulation, pop: 50,000\nlock down at 200 confirmed'
ave_active_cases = tools.plot_run_set_series(
    test_set, s.ACTIVE_CASES_SERIES, title_template)

ave_active_confirmed_cases = tools.plot_run_set_series(
    test_set, s.ACTIVE_CONFIRMED_CASES_SERIES, title_template)

ave_deaths = tools.plot_run_set_series(
    test_set, s.CUMULATIVE_DEATHS_SERIES, title_template)

title_template = '{} Simulation, pop: 50,000\nlock down at 200 confirmed, events at days 40-50, 70'
ave_active_cases_event = tools.plot_run_set_series(
    event_set, s.ACTIVE_CASES_SERIES, title_template)

ave_active_confirmed_cases_event = tools.plot_run_set_series(
    event_set, s.ACTIVE_CONFIRMED_CASES_SERIES, title_template)

ave_deaths_event = tools.plot_run_set_series(
    event_set, s.CUMULATIVE_DEATHS_SERIES, title_template)

phased_events_comp = {
    'active confirmed': ave_active_confirmed_cases,
    'active confirmed with events': ave_active_confirmed_cases_event,
    'cumulative deaths': ave_deaths,
    'cumulative deaths with events': ave_deaths_event
}

tools.plot_curves(phased_events_comp, 'comparison when events occur')
