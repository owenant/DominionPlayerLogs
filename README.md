These notebooks are used to parse data from logs of online Dominion games provided by Doug Zongker from iostropic.org.

1. MultipleLogProcessor_Simplified.ipynb - This notebook scans the player logs to find examples with a given kingdom card set and player number. It then dumps the corresponding log filenames into a text file ready for the next step.
2. GeneratePlayTracesFromLogsFiles_UsingCardCount.ipynb - This notebook takes the list of log files generated in the previous step, parses each log and generates a card count based playtrace for each player and game. It outputs all these play traces to a single text file.
3. GeneratePlayTracesFromLogsFiles_UsingActions.ipynb - This notebook takes the list of log files generated in the previous step, parses each log and generates an actions based playtrace for each player and game. It outputs all these play traces to a single text file. Note this data is converted into N-Gram based playtraces in owenant/DominionPlayTraceClustering

The result of these steps then feeds into code for analysing and clustering play traces in owenant/DominionPlayTraceClustering
