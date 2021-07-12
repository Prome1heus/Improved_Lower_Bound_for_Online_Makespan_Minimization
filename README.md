<h1> ReadMe </h1>
This Github contains the source code of a software that assists with finding a lower bound for the online makespan minimization problem. The software was written as part of my bachelor thesis at the chair of Algorithms and Complexity of the Technical University of Munich.

<h1> Introduction </h1>
The technique used for finding a lower bound for the online makespan minimization is the layering technique. The main idea is to prove that there can be no algorithm with a competitive ratio better than c on m machines by finding a job sequence divided in rounds of m jobs such that no two jobs from the same round can be scheduled on the same machine by any algorithm with a competitive ratio of at most c.
A final round containing a single job forces a competitive ratio of c.

<h1> Usage </h1>
Command line arguments
<ul>
    <li> -t or --timeout: the timeout for the CP-SAT solver in seconds </li>
    <li> -g or --greedy_ratio: if the size of a job divided by the current makespan is smaller than this ratio, greedy scheduling is used for the job</li>
    <li> -f or --final_greedy_ratio: the greedy ratio for the final subround (relevant for upscaling)</li>
</ul>

There are different ways in which the software can be used. Either to verify that a job sequence is valid for the proof or to assist with finding a job sequence. <br>
For both ways it is necessary to input the following parameters at the beginning
<ul>
    <li> The number of machines m </li>
    <li> The competitive ratio c </li>
</ul>
In order to verify the job sequence, it is necessary to specify the sub rounds of the sequence by their job size and multiplicity. <br>
<br>
It is also possible to have the software to assist with finding a job sequence. It is then only necessary to specify the size of the first job of each round. In order to indicate this mode type -1 when asked for the multiplicity.
<br>
In both modes indicate that the next job is the final one by choosing 0 as the job size. You will then be prompted for the size of the final job. <br>
<br>
In order to finish the sequence with a final job, enter 'finish' when prompted for the size of the next job.
When a sequence is finished, latex source code for the proof and illustrations for each subround will be generated. This may take a couple of seconds.