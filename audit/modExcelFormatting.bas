Option Explicit
Option Private Module

' ================================================================
' modExcelFormatting
' ================================================================


Public Sub ClearARMPIL(ByVal ws As Worksheet)
    Dim lr As Long
    lr = GetLastUsedRowInColumns(ws, 2, 7)
    
    If lr >= 6 Then
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).ClearContents
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Interior.Color = RGB(250, 251, 252)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Font.Color = RGB(44, 62, 80)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 7)).Font.Italic = False
    End If
End Sub

Public Sub ClearSELE(ByVal ws As Worksheet)
    Dim lr As Long
    lr = GetLastUsedRowInColumns(ws, 2, 5)
    
    If lr >= 6 Then
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).ClearContents
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).Interior.Color = RGB(250, 251, 252)
        ws.Range(ws.Cells(6, 2), ws.Cells(lr, 5)).Font.Color = RGB(44, 62, 80)
    End If
End Sub

Public Sub ClearAllTables()
    Dim state As AppState

    On Error GoTo Cleanup

    BeginExcelBatch state, "Limpando tabelas..."

    Dim wsArm As Worksheet
    Dim wsSel As Worksheet
    Dim wsRes As Worksheet

    Set wsArm = ThisWorkbook.Sheets("ARMPIL")
    Set wsSel = ThisWorkbook.Sheets("SELE")
    Set wsRes = ThisWorkbook.Sheets("RESULTADO")

    Dim lastRes As Long
    lastRes = wsRes.Cells(wsRes.Rows.count, 2).End(xlUp).Row
    If lastRes >= 9 Then
        wsRes.Range(wsRes.Cells(9, 2), wsRes.Cells(lastRes, 10)).FormatConditions.Delete
    End If

    ClearARMPIL wsArm
    ClearSELE wsSel
    ClearResultsPermanent wsRes

    SetArmpilManualHint wsArm
    wsArm.Cells(4, 2).Value = "  Nenhum ARMPIL carregado."
    wsSel.Cells(4, 2).Value = "  Nenhum SELE carregado."

Cleanup:
    RestoreExcelBatch state

    If Err.Number <> 0 Then
        Err.Raise Err.Number, , Err.Description
    End If
End Sub

Public Sub FormatInputRange(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long, ByVal colStart As Long, ByVal colEnd As Long)
    If rowEnd < rowStart Then Exit Sub

    With ws.Range(ws.Cells(rowStart, colStart), ws.Cells(rowEnd, colEnd))
        .Borders.LineStyle = xlContinuous
        .Borders.Weight = xlThin
        .VerticalAlignment = xlCenter
    End With
End Sub

Public Function GetLastArmpilDataRow(ByVal ws As Worksheet) As Long
    GetLastArmpilDataRow = GetLastUsedRowInColumns(ws, 2, 5)
    If GetLastArmpilDataRow < 6 Then GetLastArmpilDataRow = 5
End Function

Public Function GetPilarBlockFillColor(ByVal blockIndex As Long) As Long
    If (blockIndex Mod 2) = 0 Then
        GetPilarBlockFillColor = RGB(235, 244, 255)
    Else
        GetPilarBlockFillColor = RGB(255, 249, 232)
    End If
End Function

Public Sub ApplyPilarBlockColors(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long, ByVal pilarCol As Long, ByVal colStart As Long, ByVal colEnd As Long)
    Dim currentStart As Long
    Dim currentPilar As String
    Dim blockIndex As Long
    Dim i As Long
    Dim fillColor As Long

    If rowEnd < rowStart Then Exit Sub

    currentStart = rowStart
    currentPilar = NormalizePilarName(CStr(ws.Cells(rowStart, pilarCol).Value2))
    blockIndex = 0

    For i = rowStart + 1 To rowEnd + 1
        If i > rowEnd Or NormalizePilarName(CStr(ws.Cells(i, pilarCol).Value2)) <> currentPilar Then
            fillColor = GetPilarBlockFillColor(blockIndex)

            With ws.Range(ws.Cells(currentStart, colStart), ws.Cells(i - 1, colEnd)).Interior
                .Pattern = xlSolid
                .Color = fillColor
            End With
            currentStart = i
            blockIndex = blockIndex + 1
            If i <= rowEnd Then currentPilar = NormalizePilarName(CStr(ws.Cells(i, pilarCol).Value2))
        End If
    Next i
End Sub

Public Sub ApplyArmpilFormatting(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long)
    If rowEnd < rowStart Then Exit Sub

    Dim rg As Range
    Set rg = ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 7))

    FormatInputRange ws, rowStart, rowEnd, 2, 7

    With rg
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .Font.Color = RGB(44, 62, 80)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
    End With

    ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 2)).Font.Bold = True
    ws.Rows(rowStart & ":" & rowEnd).RowHeight = 16

    ApplyPilarBlockColors ws, rowStart, rowEnd, 2, 2, 7
End Sub

Public Sub SetArmpilManualHint(ByVal ws As Worksheet)
    With ws.Cells(3, 2)
        .Value = "Edicao manual: preencha numero do Pilar, Qtd(Qf) e Bitola(mm). O lance pode ficar em branco se a sequencia puder ser inferida. Depois rode 'Atualizar ARMPIL Manual'."
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .Font.Color = RGB(90, 90, 90)
        .Font.Italic = True
    End With
End Sub

Public Sub SortSheetRangeByPilarLance(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long, ByVal firstCol As Long, ByVal lastCol As Long, ByVal pilarCol As Long, ByVal lanceCol As Long, ByVal helperStartCol As Long)
    If rowEnd < rowStart Then Exit Sub

    Dim rowCount As Long
    rowCount = rowEnd - rowStart + 1
    If rowCount <= 1 Then Exit Sub

    Dim src As Variant
    src = ws.Range(ws.Cells(rowStart, pilarCol), ws.Cells(rowEnd, pilarCol)).Value2

    Dim helperData() As Variant
    ReDim helperData(1 To rowCount, 1 To 3)

    Dim i As Long
    For i = 1 To rowCount
        helperData(i, 1) = GetPilarSortNumber(CStr(GetArrayCell(src, i, 1)))
        helperData(i, 2) = GetPilarPrefixRank(CStr(GetArrayCell(src, i, 1)))
        helperData(i, 3) = GetPilarSuffix(CStr(GetArrayCell(src, i, 1)))
    Next i

    ws.Range(ws.Cells(rowStart, helperStartCol), ws.Cells(rowEnd, helperStartCol + 2)).Value2 = helperData

    With ws.Sort
        .SortFields.Clear
        .SortFields.Add Key:=ws.Range(ws.Cells(rowStart, helperStartCol), ws.Cells(rowEnd, helperStartCol)), SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .SortFields.Add Key:=ws.Range(ws.Cells(rowStart, helperStartCol + 1), ws.Cells(rowEnd, helperStartCol + 1)), SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .SortFields.Add Key:=ws.Range(ws.Cells(rowStart, helperStartCol + 2), ws.Cells(rowEnd, helperStartCol + 2)), SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .SortFields.Add Key:=ws.Range(ws.Cells(rowStart, lanceCol), ws.Cells(rowEnd, lanceCol)), SortOn:=xlSortOnValues, Order:=xlAscending, DataOption:=xlSortNormal
        .SetRange ws.Range(ws.Cells(rowStart, firstCol), ws.Cells(rowEnd, helperStartCol + 2))
        .Header = xlNo
        .MatchCase = False
        .Orientation = xlTopToBottom
        .Apply
    End With

    ws.Range(ws.Cells(rowStart, helperStartCol), ws.Cells(rowEnd, helperStartCol + 2)).ClearContents
End Sub

Public Sub ApplySeleFormatting(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long)
    If rowEnd < rowStart Then Exit Sub

    Dim rg As Range
    Set rg = ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 5))

    With rg
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .Font.Color = RGB(44, 62, 80)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
    End With

    ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 2)).Font.Bold = True
    ws.Rows(rowStart & ":" & rowEnd).RowHeight = 16

    ApplyPilarBlockColors ws, rowStart, rowEnd, 2, 2, 5
End Sub
