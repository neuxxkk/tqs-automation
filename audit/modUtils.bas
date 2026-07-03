Option Explicit
Option Private Module

' ================================================================
' modUtils
' ================================================================

Public Const FIRST_DATA_ROW As Long = 6
Public Const RESULT_FIRST_DATA_ROW As Long = 9
Public Const COL_PILAR As Long = 2
Public Const COL_LANCE As Long = 3
Public Const COL_QTD As Long = 4
Public Const COL_BITOLA As Long = 5
Public Const COL_AS_TOTAL As Long = 6
Public Const COL_CHAVE As Long = 7

Public Type AppState
    Calculation As XlCalculation
    ScreenUpdating As Boolean
    EnableEvents As Boolean
    StatusBar As Variant
End Type

Public Sub BeginExcelBatch(ByRef state As AppState, Optional ByVal statusText As String = "")
    state.Calculation = Application.Calculation
    state.ScreenUpdating = Application.ScreenUpdating
    state.EnableEvents = Application.EnableEvents
    state.StatusBar = Application.StatusBar

    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual
    If statusText <> "" Then Application.StatusBar = statusText
End Sub

Public Sub RestoreExcelBatch(ByRef state As AppState)
    Application.StatusBar = state.StatusBar
    Application.Calculation = state.Calculation
    Application.ScreenUpdating = state.ScreenUpdating
    Application.EnableEvents = state.EnableEvents
End Sub


Public Function IsDialogCancelled(ByVal value As Variant) As Boolean
    If VarType(value) = vbBoolean Then
        IsDialogCancelled = (CBool(value) = False)
    Else
        IsDialogCancelled = False
    End If
End Function

Public Function PickFilePath(ByVal titleText As String, ByVal filterName As String, ByVal filterPattern As String) As String
    Dim fd As FileDialog
    Set fd = Application.FileDialog(msoFileDialogFilePicker)

    fd.Title = titleText
    fd.Filters.Clear
    fd.Filters.Add filterName, filterPattern
    fd.Filters.Add "Todos", "*.*"
    fd.AllowMultiSelect = False

    If fd.Show = -1 Then PickFilePath = fd.SelectedItems(1)
End Function

Public Function GetArrayRowCount(ByVal data As Variant) As Long
    On Error GoTo ScalarValue
    GetArrayRowCount = UBound(data, 1) - LBound(data, 1) + 1
    Exit Function

ScalarValue:
    GetArrayRowCount = 1
End Function

Public Function GetArrayCell(ByVal data As Variant, ByVal rowIndex As Long, ByVal colIndex As Long) As Variant
    On Error GoTo ScalarValue
    GetArrayCell = data(rowIndex, colIndex)
    Exit Function

ScalarValue:
    If rowIndex = 1 And colIndex = 1 Then GetArrayCell = data
End Function

Public Function CountCsvItems(ByVal csvText As String) As Long
    If Trim$(csvText) = "" Then Exit Function
    CountCsvItems = UBound(Split(csvText, ",")) + 1
End Function

Public Function ReadAllNonEmptyLines(ByVal path As String) As Variant
    Dim ff As Integer
    ff = FreeFile
    
    Dim fileContent As String
    Open path For Binary Access Read As #ff
    fileContent = Space$(LOF(ff))
    Get #ff, , fileContent
    Close #ff

    ' Remove BOM UTF-8
    If Len(fileContent) >= 3 Then
        If Asc(Mid$(fileContent, 1, 1)) = 239 And _
           Asc(Mid$(fileContent, 2, 1)) = 187 And _
           Asc(Mid$(fileContent, 3, 1)) = 191 Then
            fileContent = Mid$(fileContent, 4)
        End If
    End If

    fileContent = Replace(fileContent, vbCrLf, vbLf)
    fileContent = Replace(fileContent, vbCr, vbLf)

    Dim rawLines() As String
    rawLines = Split(fileContent, vbLf)

    Dim tmp() As String
    ReDim tmp(0 To UBound(rawLines))

    Dim count As Long
    count = 0

    Dim i As Long
    Dim s As String
    For i = LBound(rawLines) To UBound(rawLines)
        s = Trim$(rawLines(i))
        If s <> "" Then
            tmp(count) = s
            count = count + 1
        End If
    Next i

    If count = 0 Then
        ReadAllNonEmptyLines = Array()
        Exit Function
    End If

    Dim result() As String
    ReDim result(0 To count - 1)

    For i = 0 To count - 1
        result(i) = tmp(i)
    Next i

    ReadAllNonEmptyLines = result
End Function

Public Function NormalizePilarName(ByVal raw As String) As String
    NormalizePilarName = UCase$(Trim$(raw))
End Function

Public Function GetNaoDimensionadoText() As String
    GetNaoDimensionadoText = "n" & ChrW$(227) & "o dimensionado"
End Function

Public Function BuildPilarKey(ByVal pilar As String, ByVal lanceValue As Variant) As String
    BuildPilarKey = NormalizePilarName(pilar) & "|" & Trim$(CStr(lanceValue))
End Function

Public Sub SortNumericVariantArray(ByRef values As Variant)
    Dim i As Long
    Dim j As Long
    Dim tmp As Variant

    If Not IsArray(values) Then Exit Sub
    If UBound(values) <= LBound(values) Then Exit Sub

    For i = LBound(values) To UBound(values) - 1
        For j = i + 1 To UBound(values)
            If CLng(values(i)) > CLng(values(j)) Then
                tmp = values(i)
                values(i) = values(j)
                values(j) = tmp
            End If
        Next j
    Next i
End Sub

Public Function JoinVariantList(ByVal values As Variant) As String
    Dim i As Long

    If Not IsArray(values) Then Exit Function

    For i = LBound(values) To UBound(values)
        JoinVariantList = JoinVariantList & CStr(values(i)) & ", "
    Next i

    If Len(JoinVariantList) >= 2 Then
        JoinVariantList = Left$(JoinVariantList, Len(JoinVariantList) - 2)
    End If
End Function

Public Function CompactPromptText(ByVal text As String, ByVal maxLen As Long) As String
    text = Trim$(text)
    If maxLen <= 0 Or Len(text) <= maxLen Then
        CompactPromptText = text
    Else
        CompactPromptText = Left$(text, maxLen - 4) & " ..."
    End If
End Function

Public Function BuildPromptListText(ByVal detailedText As String, ByVal fallbackText As String, ByVal maxLen As Long) As String
    If Trim$(detailedText) <> "" Then
        BuildPromptListText = CompactPromptText(detailedText, maxLen)
    Else
        BuildPromptListText = CompactPromptText(fallbackText, maxLen)
    End If
End Function

Public Function GetSheetLancesDict(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal colLance As Long) As Object
    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    Dim lastRow As Long
    lastRow = ws.Cells(ws.Rows.count, colLance).End(xlUp).Row
    If lastRow < rowStart Then
        Set GetSheetLancesDict = dict
        Exit Function
    End If

    Dim data As Variant
    data = ws.Range(ws.Cells(rowStart, colLance), ws.Cells(lastRow, colLance)).Value2

    Dim i As Long
    If IsArray(data) Then
        For i = 1 To UBound(data, 1)
            AddNumericLanceToDict dict, data(i, 1)
        Next i
    Else
        AddNumericLanceToDict dict, data
    End If

    Set GetSheetLancesDict = dict
End Function

Public Sub AddNumericLanceToDict(ByRef dict As Object, ByVal value As Variant)
    Dim text As String

    If IsError(value) Then Exit Sub
    If IsNull(value) Then Exit Sub
    If IsEmpty(value) Then Exit Sub
    text = Trim$(CStr(value))
    If text = "" Then Exit Sub
    If Not IsNumeric(text) Then Exit Sub

    dict(CLng(text)) = True
End Sub

Public Function DetectDelim(ByVal firstLine As String) As String
    If InStr(firstLine, ";") > 0 Then
        DetectDelim = ";"
    Else
        DetectDelim = ","
    End If
End Function

Public Function CleanCSV(ByVal s As String) As String
    s = Trim$(s)
    If Len(s) >= 2 Then
        If Left$(s, 1) = Chr$(34) And Right$(s, 1) = Chr$(34) Then
            s = Mid$(s, 2, Len(s) - 2)
        End If
    End If
    CleanCSV = Replace(Trim$(s), ",", ".")
End Function

Public Function GetRequiredWorksheet(ByVal sheetName As String) As Worksheet
    On Error Resume Next
    Set GetRequiredWorksheet = ThisWorkbook.Worksheets(sheetName)
    On Error GoTo 0

    If GetRequiredWorksheet Is Nothing Then
        Err.Raise vbObjectError + 2100, , "A aba '" & sheetName & "' nao foi encontrada nesta pasta de trabalho."
    End If
End Function

Public Function BuildStageSuffix(ByVal stage As String) As String
    If Trim$(stage) <> "" Then BuildStageSuffix = " na etapa '" & stage & "'"
End Function

Public Function GetLastUsedRowInColumns(ByVal ws As Worksheet, ByVal colStart As Long, ByVal colEnd As Long) As Long
    Dim col As Long
    Dim candidate As Long

    For col = colStart To colEnd
        candidate = ws.Cells(ws.Rows.count, col).End(xlUp).Row
        If candidate > GetLastUsedRowInColumns Then GetLastUsedRowInColumns = candidate
    Next col
End Function

Public Function WorksheetHasDataRows(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal colStart As Long, ByVal colEnd As Long) As Boolean
    WorksheetHasDataRows = (GetLastUsedRowInColumns(ws, colStart, colEnd) >= rowStart)
End Function

Public Function GetPilarSortNumber(ByVal pilar As String) As Double
    Dim txt As String
    Dim pos As Long
    Dim digits As String

    txt = NormalizePilarName(pilar)
    If Left$(txt, 3) = "PAF" Then
        pos = 4
    ElseIf Left$(txt, 1) = "P" Then
        pos = 2
    Else
        pos = 1
    End If

    Do While pos <= Len(txt) And Mid$(txt, pos, 1) Like "#"
        digits = digits & Mid$(txt, pos, 1)
        pos = pos + 1
    Loop

    If digits = "" Then
        GetPilarSortNumber = 1000000000#
    Else
        GetPilarSortNumber = CDbl(digits)
    End If
End Function

Public Function GetPilarPrefixRank(ByVal pilar As String) As Long
    Dim txt As String
    txt = NormalizePilarName(pilar)

    If Left$(txt, 1) = "P" And Left$(txt, 3) <> "PAF" Then
        GetPilarPrefixRank = 0
    ElseIf Left$(txt, 3) = "PAF" Then
        GetPilarPrefixRank = 1
    Else
        GetPilarPrefixRank = 9
    End If
End Function

Public Function GetPilarSuffix(ByVal pilar As String) As String
    Dim txt As String
    Dim pos As Long

    txt = NormalizePilarName(pilar)
    If Left$(txt, 3) = "PAF" Then
        pos = 4
    ElseIf Left$(txt, 1) = "P" Then
        pos = 2
    Else
        pos = 1
    End If

    Do While pos <= Len(txt) And Mid$(txt, pos, 1) Like "#"
        pos = pos + 1
    Loop

    GetPilarSuffix = Mid$(txt, pos)
End Function
