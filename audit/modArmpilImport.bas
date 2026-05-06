Option Explicit
Option Private Module

' ================================================================
' modArmpilImport
' ================================================================


Public Sub LoadArmpil(ByVal path As String)
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("ARMPIL")

    Dim state As AppState

    On Error GoTo TrataErro

    BeginExcelBatch state, "Carregando ARMPIL..."

    ClearARMPIL ws
    SetArmpilManualHint ws

    Dim lines As Variant
    lines = ReadAllNonEmptyLines(path)

    If Not IsArray(lines) Then GoTo SaidaSegura
    If UBound(lines) < LBound(lines) Then GoTo SaidaSegura

    Dim delim As String
    delim = DetectDelim(CStr(lines(LBound(lines))))

    Dim startIdx As Long
    startIdx = LBound(lines)

    Dim firstField As String
    firstField = LCase$(Trim$(Replace(Split(CStr(lines(LBound(lines))), delim)(0), Chr$(34), "")))
    If firstField = "pilar" Then startIdx = startIdx + 1

    Dim maxRows As Long
    maxRows = UBound(lines) - startIdx + 1
    If maxRows <= 0 Then GoTo SaidaSegura

    Dim dataOut() As Variant
    ReDim dataOut(1 To maxRows, 1 To 4)

    Dim i As Long
    Dim outRow As Long
    outRow = 0

    Dim parts() As String
    Dim pilar As String

    For i = startIdx To UBound(lines)
        parts = Split(CStr(lines(i)), delim)

        If UBound(parts) >= 3 Then
            pilar = NormalizePilarName(CleanCSV(parts(0)))

            If pilar <> "" And LCase$(pilar) <> "pilar" Then
                outRow = outRow + 1

                dataOut(outRow, 1) = pilar
                dataOut(outRow, 2) = CLng(Val(CleanCSV(parts(1))))
                dataOut(outRow, 3) = CDbl(Val(CleanCSV(parts(2))))
                dataOut(outRow, 4) = CDbl(Val(CleanCSV(parts(3))))
            End If
        End If
    Next i

    If outRow = 0 Then GoTo SaidaSegura

    RenderArmpilRows ws, dataOut, outRow, "  Carregado: " & outRow & " registros  |  delimitador: [" & delim & "]  |  " & path

SaidaSegura:
    RestoreExcelBatch state
    Exit Sub

TrataErro:
    RestoreExcelBatch state
    MsgBox "Erro em LoadArmpil: " & Err.Description, vbExclamation
End Sub

Public Sub RenderArmpilRows(ByVal ws As Worksheet, ByVal dataOut As Variant, ByVal rowCount As Long, ByVal statusText As String)
    Dim lastRow As Long
    Dim renderData() As Variant
    Dim i As Long
    Dim j As Long

    If rowCount <= 0 Then Exit Sub

    lastRow = FIRST_DATA_ROW + rowCount - 1

    ReDim renderData(1 To rowCount, 1 To 4)
    For i = 1 To rowCount
        For j = 1 To 4
            renderData(i, j) = dataOut(i, j)
        Next j
    Next i

    ws.Range("B" & FIRST_DATA_ROW).Resize(rowCount, 4).Value = renderData
    ws.Range("F" & FIRST_DATA_ROW & ":F" & lastRow).FormulaR1C1 = "=RC[-2]*PI()*(RC[-1]^2)/4/100"
    ws.Range("G" & FIRST_DATA_ROW & ":G" & lastRow).FormulaR1C1 = "=UPPER(TRIM(RC[-5]))&""|""&RC[-4]"
    ws.Range("F" & FIRST_DATA_ROW & ":G" & lastRow).Calculate

    SortSheetRangeByPilarLance ws, FIRST_DATA_ROW, lastRow, COL_PILAR, COL_CHAVE, COL_PILAR, COL_LANCE, COL_CHAVE + 1
    ws.Range("F" & FIRST_DATA_ROW & ":G" & lastRow).Calculate

    ws.Range("C" & FIRST_DATA_ROW & ":C" & lastRow).NumberFormat = "0"
    ws.Range("D" & FIRST_DATA_ROW & ":E" & lastRow).NumberFormat = "0.00"
    ws.Range("F" & FIRST_DATA_ROW & ":F" & lastRow).NumberFormat = "0.00"

    ApplyArmpilFormatting ws, FIRST_DATA_ROW, lastRow
    ws.Cells(4, COL_PILAR).Value = statusText
End Sub
