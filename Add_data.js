/*
Creates a Date Stamp if a column is edited. Removes Date Stamp, if cell value is removed
Based on:
https://yagisanatode.com/2018/02/21/add-the-current-date-to-a-sheet-when-data-is-added-so-that-the-date-does-not-changestatic-google-sheets/
*/


//CORE VARIABLES
// The column you want to check if something is entered.
var COLUMNTOCHECK = 1;
// Where you want the date time stamp offset from the input location. [row, column]
var DATETIMELOCATION = [0,2];
 
function onEdit(e) 
{
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  //checks that we're on the correct sheet.
  var selectedCell = ss.getActiveCell(); //this is Range class
  //checks the column to ensure it is on the one we want to cause the date to appear.
  if( selectedCell.getColumn() == COLUMNTOCHECK) 
  { 
    var dateTimeCell = selectedCell.offset(DATETIMELOCATION[0],DATETIMELOCATION[1]);
    if( selectedCell.getDisplayValue() == '')
    {
      dateTimeCell.setValue('');
    }
    else
    {
      dateTimeCell.setValue(new Date());
    }
  }
}
