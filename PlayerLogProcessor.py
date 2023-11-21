from bs4 import BeautifulSoup
import re

def processor_log_file(input_dir, html_doc, output_dir):
    #output file
    #set-up output file for high level info including card supply
    high_level_output_file = html_doc[:-5] + '_summary.txt'
    
    #set-up output file for features - i.e. number of cards at the end of each round
    #TODO:
        
    #read and parse html
    file = open(input_dir + '/' + html_doc, mode = 'r')
    soup = BeautifulSoup(file, 'html.parser')
    
    #convert html contents into a list of tabs, navigable strings etc
    pre_tag = soup.find('pre')
    pre_tag.contents
    
    #first extract number of players and final score
    #look for entries of the form #n <name>: x points' - these are tagged with a 'b'
    #in earlier log files the '#n' is dropped and hence we also need to consider this case
    players = []
    scores = []
    list_b_tags = soup.find_all('b');
    for tag in list_b_tags:
        s = tag.text
        if '#' in s:
            #extract name (assume string of form '#n ' comes before the name)
            players.append(s[3:])
            #next sibing contains the score, assume score is after a string of the form ': ' and is 2 digits long
            score_text = tag.next_sibling
            scores.append(score_text[2:4])

    #deal with second case where name is not preceeded by a '#n '
    if len(players) == 0:
        for tag in list_b_tags:
            s = tag.text
            if ':' in s:
                #in this case the name is contained in the text preceeded by a ':'
                colon_position = s.index(':')
                players.append(s[:colon_position])
                scores.append(s[colon_position+1 : colon_position+3])
    
    #extract number of turns for this game for each player
    total_turns = []
    count = 0
    for (k,r) in enumerate(pre_tag.contents):
        if 'turn' in r.text:
            turn_position = r.text.index('turn')
            #assume number of turns is given by two digits and there is a space to the start of the word 'turn'
            total_turns.append(int(re.search(r'\d+', r.text[turn_position-3:turn_position]).group()))
            count += 1
            if count == len(players):
                break
            
    #note, turns are in same order as player names in html file
    turns_by_player = {}
    turns_by_player[players[0]] = total_turns[0]
    turns_by_player[players[1]] = total_turns[1]
    
    
    #following function parses a single line which consists of number of cards (unless equal to one) and card types
    #each separated by a colon and ended with a full stop or a horizontal dashed line. It returns a list of cards 
    #with card names duplicated according to the number of them in the row. Also the index of the full stop or 
    #dashed line will be returned
    def parse_row_into_cards(contents_list):
        card_list = []
        for (k,r) in enumerate(contents_list):
            #Need to be careful that the first content item doesn't contain a '....', causing 
            #the code to pickup a full stop
            if ((('.' not in r) or (k == 0)) and r.name == None and ('----------------------' not in r)):
                #check to see if trashing text contains the number of cards trashed
                #number is contained in last two digits of text
                try:
                    no_cards = int(r[-2:])
                except ValueError:
                    no_cards = 1
                #take next entry along which should be the card name
                card_type = r.next_sibling.text
                #and add copies of that to the dictionary
                for count in range(0,no_cards):
                    card_list.append(card_type)
            elif (('.' in r) or ('----------------------' in r)) and (k != 0):
                return (k, card_list)
    
    #next extract kingdom cards - first we deal with the case where the default set is chosen and players don't 
    #make changes
    
    #so we need to be careful figuring out the cards in the supply, first we scan down the file
    # to see if there is a 'chosen cards are' string followed by ''<player name> vetoes'. In this
    #case the players are making choices over the card supply, if this isnt present then the
    #supply cards are given at the top of the file post a string that says 'cards in supply'

    #start with the case where players can veto
    vetoes_used = False
    for (i,s) in enumerate(pre_tag.contents):
        if 'chosen cards are' in s:
            #loop over chosen supply cards
            (index, cards) = parse_row_into_cards(pre_tag.contents[i:])
            index_end = i + index 
            supply_cards = cards
            vetoes_used = True
    
    if vetoes_used == True:
        #next each player can veto a card
        vetoed_cards = []
        for player in players:
            for s in pre_tag.contents[index_end:]:
                check_string = player + ' vetoes'
                if check_string in s:
                    vetoed_cards.append(s.next_sibling.text)
        #remove vetoed cards from list of supply cards
        supply_cards = list(filter(lambda x: x not in vetoed_cards, supply_cards))
            
    #if this didnt occur move onto the second case
    if vetoes_used == False:
        for i, s in enumerate(pre_tag.contents):
            if 'cards in supply' in s:
                (index, cards) = parse_row_into_cards(pre_tag.contents[i:])
                supply_cards = cards

    #use a dictionary of dictionaries to track gained cards by turn by player, and initialise keys
    incremental_cards_by_turn = {}
    for player in players:
        incremental_cards_by_turn[player] = {}
        for turn in range(1,turns_by_player[player]+1):
            incremental_cards_by_turn[player][turn] = {}
            incremental_cards_by_turn[player][turn] = {}
            incremental_cards_by_turn[player][turn] = {}
            incremental_cards_by_turn[player][turn] = {}
        for turn in range(1,turns_by_player[player]+1):
            incremental_cards_by_turn[player][turn]['buys'] = {}
            incremental_cards_by_turn[player][turn]['trashing'] = {}
            incremental_cards_by_turn[player][turn]['gaining'] = {}
            incremental_cards_by_turn[player][turn]['trashes'] = {}
        
    for player in players:
        turn_counter = 1
        #string to check for a buy action
        check_buy = player + ' buys'
        #string to check if current player is trashing a card
        check_trashing = 'trashing'
        #string to check if current player is gaining a card
        check_gaining = 'gaining'
        #string to check if another player trashes a card. Howver, current player can both 'trashes' 
        #and 'trashing'. Also it is possible for a player to trash nothing
        check_player_trashes = [x + ' trashes' for x in players] # need to check this!
        #string to check if another player is gains a card (gains is used rather than
        #gaining when a player gets a card out of turn)
        check_player_gains = [ x + ' gains' for x in players]
        #string to check end of turn
        check_turn_end = '(' + player + ' draws:'
        for (i,p) in enumerate(pre_tag.contents):
            check_turn = player + '\'s' + ' turn ' + str(turn_counter)
            if check_turn in p:
                buy_card_list = []
                trashing_card_list = []
                gaining_card_list = []
                gains_card_list = {} #needs to be a dictionary as multiple players may gain in another player's round
                trashes_card_list = {} #needs to be a dictionary as multiple players may need to trash in another player's round
                for player_ in players:
                    gains_card_list[player_] = [] 
                    trashes_card_list[player_] = [] 
                for (j,q) in enumerate(pre_tag.contents[i:]):
                    player_gains_list = [ x in q for x in check_player_gains]
                    player_trashes_list = [ x in q for x in check_player_trashes]
                    if check_buy in q:
                        (index, cards) = parse_row_into_cards(pre_tag.contents[i + j:])
                        buy_card_list.append(cards)
                    elif check_trashing in q:
                        if 'trashing nothing' in r:
                            break
                        (index, cards) = parse_row_into_cards(pre_tag.contents[i + j:])
                        trashing_card_list.append(cards)
                    elif check_gaining in q:
                        #also we need to check for a 'gaining nothing' case
                        if 'gaining nothing' in r:
                            break
                        else:
                            (index, cards) = parse_row_into_cards(pre_tag.contents[i + j:])
                            gaining_card_list.append(cards)
                    elif any(player_gains_list):
                        #next we check if an opponent gains a card, e.g. a curse card
                        #need to loop through opponents
                        for (index, player_gains_check) in enumerate(player_gains_list):
                            if player_gains_check == True:
                                player_ = players[index]
                                (index_, cards) = parse_row_into_cards(pre_tag.contents[i + j:])
                                gains_card_list[player_].append(cards)
                    elif any(player_trashes_list):
                        #next we check if an opponent trashes a card
                        for (index, player_trashes_check) in enumerate(player_trashes_list):
                            if player_trashes_check == True:
                                player_ = players[index]
                                (index_, cards) = parse_row_into_cards(pre_tag.contents[i + j:])
                                trashes_card_list[player_].append(cards)
                    elif check_turn_end in q.text:
                        incremental_cards_by_turn[player][turn_counter]['buys'] = buy_card_list
                        incremental_cards_by_turn[player][turn_counter]['trashing'] = trashing_card_list
                        incremental_cards_by_turn[player][turn_counter]['gaining'] = gaining_card_list
                        for player_ in gains_card_list.keys():
                            incremental_cards_by_turn[player_][turn_counter]['gains'] = gains_card_list[player_] 
                        for player_ in trashes_card_list.keys():
                            incremental_cards_by_turn[player_][turn_counter]['trashes'] = trashes_card_list[player_] 
                        turn_counter += 1
                        break
    
    #finally we flatten incremental_cards_by_turn into a dictionary of lists
    for player in players:
        for turns in range(1, turns_by_player[player]+1):
            for cmd_type in incremental_cards_by_turn[player][turns].keys():
                flattened_list = [item for sublist in incremental_cards_by_turn[player][turns][cmd_type] for item in sublist]
                incremental_cards_by_turn[player][turns][cmd_type] = flattened_list
    
    #first categorise supply cards if possible
    supply_sets= {}
    supply_sets['SizeDistortion'] = ['Artisan', 'Bandit', 'Bureaucrat', 'Chapel', 'Festival', 'Gardens', 'Sentry', 
                                        'Throne Room', 'Witch','Workshop']
    
    def check_known_supply_set(supply_sets_dict, cards):
        # Sort both lists
        for card_set in supply_sets_dict.keys():
            sorted_card_set = sorted(supply_sets_dict[card_set])
            sorted_cards = sorted(cards)
            # Compare the sorted lists
            if sorted_card_set == sorted_cards:
                return card_set
        return 'Unmatched'
        
    #first output high level information, including number of players, the set of supply cards and if the set of 
    #supply cards is recognised
    supply_set_match = check_known_supply_set(supply_sets, supply_cards)
    output_file = output_dir  + supply_set_match + '/' + high_level_output_file
    with open(output_file, 'w') as file:
        file.write('Input log: ' + html_doc + '\n')
        file.write('Number of Players: ' + str(len(players)) + '\n')
        file.write('Final Scores: ' + ','.join(scores)+ '\n')
        file.write('Supply cards: ' + ','.join(supply_cards)+ '\n')
        
    return None


