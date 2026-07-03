// #include <stdio.h>
// #include<math.h>
char main(int a)
{
    char grade;
    float subject1, subject2, subject3;
    float total, average, percentage;

    subject1 = 45;
    subject2 = 67;
    subject3 = 80;

    // It will calculate the Total, Average and Percentage
    total = subject1 + subject2 + subject3;
    average = total / 5.0;
    percentage = (total / 500.0) * 100;

    // It will calculate the Grade
    if (average >= 90)
        grade = 'A' ;
    else if (average >= 80 && average < 90)
        grade = 'B' ;
    else if (average >= 70 && average <= 80)
        grade = 'C' ;
    else if (average > 60 && average <= 70)
        grade = 'D' ;
    else
        grade = 'E' ;
    // It will produce the final output

    return grade;
}