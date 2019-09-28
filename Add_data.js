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

var exclude_these_sheets_from_dataStamping = ['instructions', 'sugg']
/* This does not work as needed, because it ignores operation on entire ranges. 
Bellow I suggest function that can do something about it:
e.range - https://developers.google.com/apps-script/guides/triggers/events, https://developers.google.com/apps-script/reference/spreadsheet/range
getActiveRangeList() - https://developers.google.com/apps-script/reference/spreadsheet/sheet.html#getActiveRangeList()
https://stackoverflow.com/questions/34659118/google-sheets-script-select-multiple-a1-notation-range
https://towardsdatascience.com/google-sheet-data-warehouse-c22bb2cce4b0
https://developers.google.com/apps-script/reference/spreadsheet/data-validation-builder
Google Form
*/
function onEdit(e) 
{
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  //checks that we're on the correct sheet.
  var selectedCell = ss.getActiveCell(); //this is Range class
  //checks the column to ensure it is on the one we want to cause the date to appear.
  if( exclude_these_sheets_from_dataStamping.indexOf(sheet.getSheetName()) == -1 )
  {
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
}

  
