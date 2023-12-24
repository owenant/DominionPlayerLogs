These notebooks are used to parse data from logs of online Dominion games provided by Doug Zongker from iostropic.org.

1. IdentifyLogsWithGivenSupplyAndPlayerName.ipynb - This notebook scans the player logs to find examples with a given kingdom card set and player number. It then dumps the corresponding log filenames into a txt ready for the next step.
2. GeneratePlayTracesFromLogsFiles.ipynb - This notebook takes the list of log files generated in the previous step, parses each log and generates a play trace for each player. It outputs all these play traces to a single text file.

The result of step 2 above then feeds into code for analysing play traces in my other repo 'PlayTraces'.
