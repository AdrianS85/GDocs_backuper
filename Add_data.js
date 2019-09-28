/*
Creates a Date Stamp if a column is edited. Removes Date Stamp, if cell value is removed
Based on:
https://yagisanatode.com/2018/02/21/add-the-current-date-to-a-sheet-when-data-is-added-so-that-the-date-does-not-changestatic-google-sheets/
*/


//CORE VARIABLES
// The column you want to check if something is entered.

/* This does not work as needed, because it ignores operation on entire ranges. 
Bellow I suggest function that can do something about it:
e.range - https://developers.google.com/apps-script/guides/triggers/events, https://developers.google.com/apps-script/reference/spreadsheet/range
getActiveRangeList() - https://developers.google.com/apps-script/reference/spreadsheet/sheet.html#getActiveRangeList()
https://stackoverflow.com/questions/34892925/apply-google-app-script-function-to-range-of-cells <- interate through the cells?
https://stackoverflow.com/questions/34659118/google-sheets-script-select-multiple-a1-notation-range
https://towardsdatascience.com/google-sheet-data-warehouse-c22bb2cce4b0
https://developers.google.com/apps-script/reference/spreadsheet/data-validation-builder
Google Form
*/
function onEdit(e) 
{
  var column_to_check = 1;
  // Where you want the date time stamp offset from the input location. [row, column]
  var datetime_location = [0,2];
  
  var exclude_these_sheets_from_dataStamping = ['instructions', 'sugg']
  
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  
  //checks that we're on the correct sheet.
  if( exclude_these_sheets_from_dataStamping.indexOf(sheet.getSheetName()) == -1 )
  {
    
    var selected_cells_list = ss.getActiveRangeList(); 
    
    var nb_of_ranges = selected_cells_list.getRanges().length; //This does not register multiple ranges
    
    for (var ass = 0; ass < nb_of_ranges; ass++) 
    {
      
      var selected_cells = selected_cells_list.getRanges()[ass]
      var numRows = selected_cells.getNumRows();
      var numCols = selected_cells.getNumColumns();  
      
      //These two ugly bastards iterate through Range class. Wow. Much elegant. Really no better way? 
      //its no python, i tell you hwhat...
      //Also: Its as slow as diarrhea dripping out if buffallo's ass. try setValues(values) perhaps?
      for (var i = 1; i <= numRows; i++) 
      {
        for (var j = 1; j <= numCols; j++) 
        {
          
          var current_cell = selected_cells.getCell(i,j);
          
          //Oh Lord, the nested everything, the humanity! Think of the children!
          if( current_cell.getColumn() == column_to_check) 
          {
            var dateTimeCell = current_cell.offset(datetime_location[0],datetime_location[1]);
            if( current_cell.getDisplayValue() == '')
            {
              dateTimeCell.setValue('');
            }
            else
            {
              //dateTimeCell.setValue(new Date());
              dateTimeCell.setValue(nb_of_ranges);
            }
          }
        }
      }
    }
  }
}
