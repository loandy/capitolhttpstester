#!/usr/bin/env python
#
# this is terrible --timball@sunlightfoundation.com
# GNU GPL v2.0
# but you probably shouldn't use this code for anything, it's terrible.
#
#----------------------------------------------------------

import sys
import os
import time
import io
import codecs
import json
import re
from collections import defaultdict
from fnmatch import translate as xlate
from jinja2 import Environment, FileSystemLoader

def get_letter_grades():
    """
    Convenience function. Retrieves list of possible letter grades.
    """
    global grade_settings

    return grade_settings['letter_grade_emoji'].keys()

def get_score_letter_grade(score):
    """
    Convenience function. Retrieves letter grade corresponding to a given
    score.
    """
    global grade_settings

    return grade_settings['score_letter_grades'][score]['letter_grade']

def calculate_score(site):
    """
    tests for states and returns an intervalue based on how bad things are
    this might be better served in capitolhttpstester.py but here we are
    this is the scoring mechanism for the survey
    """
    score = 100 # everyone fails hard

    # doodling while getting regex right
    body_url = 'http://www.%s.gov' % (site['body'])
    body_url_r = xlate(body_url + '*')
    https_url = site['url']
    http_url = https_url.replace('https://', 'http://')
    re_g  = xlate(http_url + '*')
    re_g = re_g.replace('www\.', '(www\.)?')

    # best case
    if (    site['hostname_match']
        and site['http status'] == 200
        and site['redirects'] == False
        and site['mixed content'] == False
        and site['non-rel links'] == False):
            score = 0
    # valid cert non-rel http links
    elif (  site['hostname_match']
        and site['http status'] == 200
        and site['redirects'] == False
        and site['mixed content'] == False
        and site['non-rel links'] == True):
            score = 1
    # valid cert mixed content
    elif (  site['hostname_match']
        and site['http status'] == 200
        and site['redirects'] == False
        and site['mixed content'] == True):
        # and site['non-rel links'] == False): # don't care if non-rel links
            score = 2
    # valid cert enforced non-ssl redirect to member site
    elif (  site['hostname_match']
        and site['redirects'] == True
        and re.match(re_g, site['redirect_url'], re.I|re.DOTALL)):
            score = 3
    # invalid cert enforced non-ssl redirect to member site
    elif (  site['hostname_match'] == False
        and site['redirects'] == True
        and re.match(re_g, site['redirect_url'], re.I|re.DOTALL)):
            score = 6
    # valid cert hard fail to leg body website
    elif (  site['hostname_match']
        and site['redirects'] == True
        and re.match(body_url_r, site['redirect_url'], re.I|re.DOTALL)):
            score = 7
    # invalid cert but SSL ready
    elif (  site['hostname_match'] == False
        and site['http status'] == 200
        and site['redirects'] == False
        and site['mixed content'] == False
        and site['non-rel links'] == False):
            score = 4
    # invalid cert content fixable
    elif (  site['hostname_match'] == False
        and site['http status'] == 200
        and site['redirects'] == False):
            score = 5
    # invalid cert hard fail to leg body website
    elif (  site['hostname_match'] == False
        and site['redirects'] == True
        and re.match(body_url_r, site['redirect_url'], re.I|re.DOTALL)):
            score = 8
    # valid cert and 4XX or 5XX response
    elif (  site['hostname_match']
        and site['http status'] >= 400
        and site['redirects'] == False):
            score = 9
    # invalid cert and 4XX or 5XX response
    elif (  site['hostname_match'] == False
        and site['http status'] >= 400
        and site['redirects'] == False):
            score = 10
    # SSL FAIL
    elif ('cipher' not in site):
            score = 11
    else:
        score = 12 # mark of the beast

    return score

def generate_evaluation(sites):
    """
    Generate an evaluation for a Congressional entity based on the given
    site list.
    """
    # Initialize evaluation.
    evaluation = dict.fromkeys(get_letter_grades())
    for letter_grade in evaluation:
        evaluation[letter_grade] = {
            'count': 0,
            'percentage': 0.0,
        }

    # Collection of site count buckets for each letter grade.
    grade_counts = defaultdict(int)

    # Overall site count.
    site_total = 0

    # Overall percentage. Not necessary since this should always become 1.0
    # (100%) by the end of the function, but it can be used to signal if
    # something is deeply wrong.
    percentage_total = 0.0

    for site in sites:
        score = calculate_score(site)
        letter_grade = get_score_letter_grade(score)

        grade_counts[letter_grade] += 1
        site_total += 1

    # Calculate stats for each letter grade.
    for letter_grade in grade_counts:
        evaluation[letter_grade]['count'] = grade_counts[letter_grade]
        percentage = round(float(evaluation[letter_grade]['count']) / float(site_total) * 100, 1)
        evaluation[letter_grade]['percentage'] = percentage
        percentage_total += percentage

    evaluation['total_count'] = site_total
    evaluation['total_percentage'] = percentage_total

    return evaluation

def generate_overall_evaluation(evaluations):
    """
    Generates an overall evaluation of all sites. Somewhat not DRY.
    """
    letter_grades = get_letter_grades()
    overall_evaluation = dict.fromkeys(letter_grades)
    overall_site_total = 0
    overall_percentage_total = 0.0

    for entity, evaluation in evaluations.items():
        overall_site_total += evaluation['total_count']

    for letter_grade in letter_grades:
        overall_evaluation[letter_grade] = {
            'count': 0,
            'percentage': 0.0,
        }

        for entity, evaluation in evaluations.items():
            overall_evaluation[letter_grade]['count'] += evaluation[letter_grade]['count']

        percentage = round(float(overall_evaluation[letter_grade]['count']) / float(overall_site_total) * 100, 1)
        overall_evaluation[letter_grade]['percentage'] = percentage
        overall_percentage_total += percentage

    overall_evaluation['total_count'] = overall_site_total
    overall_evaluation['total_percentage'] = overall_percentage_total

    return overall_evaluation

def get_congressional_entity_evaluations(congressional_entities):
    """
    Generate evaluations for each Congressional entity.
    """
    evaluations = {}

    for entity, sites in congressional_entities.items():
        evaluations[entity] = generate_evaluation(sites)

    # Generates evaluation with combined data.
    evaluations['overall'] = generate_overall_evaluation(evaluations);

    return evaluations

def get_congressional_entities(filename):
    """
    Retrieves sites for all Congressional entities from JSON data source.
    """
    if not filename:
        filename = 'output.json'

    fh = codecs.open(filename, 'r', 'utf-8')
    site_records = json.load(fh)

    congressional_entities = {
        'senators': [],          # senate members
        'representatives': [],   # house members
        'senate_committees': [], # senate committees
        'house_committees': [],  # house committees
        'joint_committees': [],  # joint committees
        'leadership': [],
        'support_office': [],
    }

    # first sort out the json pile
    while site_records:
        site = site_records.pop(0)
        if (site['body'] == 'senate' and site['type'] == 'member'):
            congressional_entities['senators'].append(site)
        elif (site['body'] == 'house' and site['type'] == 'member'):
            congressional_entities['representatives'].append(site)
        elif (site['body'] == 'senate' and site['type'] == 'committee'):
            congressional_entities['senate_committees'].append(site)
        elif (site['body'] == 'house' and site['type'] == 'committee'):
            congressional_entities['house_committees'].append(site)
        elif (site['body'] == 'house' and site['type'] == 'Minority committee'):
            congressional_entities['house_committees'].append(site)
        elif site['body'] == 'joint':
            congressional_entities['joint_committees'].append(site)
        elif (site['type'] == 'leadership'):
            site['body'] = 'leadership'
            site['type'] = 'office'
            congressional_entities['leadership'].append(site)
        elif (site['type'] == 'support'):
            site['body'] = 'support'
            site['type'] = 'office'
            congressional_entities['support_office'].append(site)

    return congressional_entities

def get_scored_sites(sites):
    """
    Add scores to given site list.
    """
    for i, site in enumerate(sites):
        score = calculate_score(site)
        sites[i]['score'] = score

    return sites

def get_scored_congressional_entities(congressional_entities):
    """
    Add scores to all sites for the given Congressional entities.
    """
    for entity, sites in congressional_entities.items():
        scored_sites = get_scored_sites(sites)
        congressional_entities[entity] = scored_sites

    return congressional_entities

def main(argv):
    global grade_settings

    grade_settings = {
        'emoji': {
            'emoji_chk': 'status-ok',
            'emoji_hrm': 'emoji-1',
            'emoji_sad': 'emoji-2',
            'emoji_bad': 'emoji-3',
            'emoji_lrt': 'status-alert',
            'emoji_exx': 'status-x',
        },
        'letter_grade_emoji': {
            'A': {
                'emoji': 'emoji_chk',
            },
            'B': {
                'emoji': 'emoji_hrm',
            },
            'C': {
                'emoji': 'emoji_sad',
            },
            'D': {
                'emoji': 'emoji_bad',
            },
            'F': {
                'emoji': 'emoji_exx',
            },
            'X': {
                'emoji': 'emoji_lrt',
            },
        },
        'score_letter_grades': {
            0: {
                'letter_grade': 'A',
                'explanation': 'OKAY Great Job!',
            },
            1: {
                'letter_grade': 'B',
                'explanation': 'SSL worked, page has insecure non-relative internal links',
            },
            2: {
                'letter_grade': 'B',
                'explanation': 'SSL worked, page has mixed content',
            },
            3: {
                'letter_grade': 'C',
                'explanation': 'SSL worked, but redirected to insecure homepage',
            },
            4: {
                'letter_grade': 'D',
                'explanation': 'Invalid cert, content okay',
            },
            5: {
                'letter_grade': 'D',
                'explanation': 'Invalid cert, page has mixed conent',
            },
            6: {
                'letter_grade': 'D',
                'explanation': 'Invalid cert, redirected to insecure homepage',
            },
            7: {
                'letter_grade': 'F',
                'explanation': 'Valid cert, but redirected to generic chamber homepage',
            },
            8: {
                'letter_grade': 'F',
                'explanation': 'Invalid cert, and redirected to generic chamber homepage',
            },
            9: {
                'letter_grade': 'F',
                'explanation': 'Valid cert, server returned error',
            },
            10: {
                'letter_grade': 'F',
                'explanation': 'Invalid cert, server returned error',
            },
            11: {
                'letter_grade': 'F',
                'explanation': 'Unable to make SSL connection',
            },
            12: {
                'letter_grade': 'X',
                'explanation': 'Unobtainable and scary dragons',
            },
        },
    }

    # Determine the source file for result data.
    if len(argv) == 1:
        filename = argv[0]
    else:
        filename = 'output.json'

    # Retrieve timestamp of the result data.
    timestamp = time.ctime(os.path.getmtime(filename))

    # Retrieve Congressional entities and generate all scores/evaluations.
    congressional_entities = get_scored_congressional_entities(get_congressional_entities(filename))
    evaluations = get_congressional_entity_evaluations(congressional_entities)

    # Grab the template to display test result data.
    environment = Environment(loader=FileSystemLoader('templates/'))
    template = environment.get_template('test_results_template.html')

    template_variables = {
        'timestamp': timestamp,
        'column_headers': [
            'Name',               # data['name'] + data['url']
            'Emoji',              # emoji column
            # calculated CHECK (works 100% no issues),
            # sad emoji (mixed content),
            # confused emoji (invalid ssl but no mixed content),
            # bounce emoji (redirected away from https),
            # poop emoji (nothing works),
            # skull&cross (4XX,5XX errors)
            'Grade',
            'Valid SSL Cert',     # data['hostname_match']
            'HTTP Status',        # data['http status']
            'Redirect To',        # data['redirects'] + data['redirect_url']
            'Mixed Content',      # data['mixed content']
            'Non-Relative Links', # data['non-rel links']
            'Issues',             # data['SSL issues']
        ],
        'report_card_headers': [
            'Grade',
            'Emoji',
            'Count',
            'Percentage',
        ],
        'congressional_entities': congressional_entities,
        'evaluations': evaluations,
    }

    # Append grade information to values injected into template.
    template_variables.update(grade_settings)

    # Inject values into template and write results to file.
    rendered_template_save_path = 'rendered/test_results.html'
    rendered_template = template.render(template_variables)
    fh = codecs.open(rendered_template_save_path, 'w', 'utf-8')
    fh.write(rendered_template)

if __name__ == '__main__':
    main(sys.argv[1:])
