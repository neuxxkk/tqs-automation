Option Explicit
Option Private Module

' ================================================================
' modComparacaoResultado
' ================================================================


Public Function CompareAndMark(Optional ByVal showSuccessMessage As Boolean = True) As Boolean
    Dim state As AppState

    BeginExcelBatch state

    On Error GoTo Cleanup

    Dim wsArm As Worksheet, wsSel As Worksheet, wsRes As Worksheet
    Set wsArm = GetRequiredWorksheet("ARMPIL")
    Set wsSel = GetRequiredWorksheet("SELE")
    Set wsRes = GetRequiredWorksheet("RESULTADO")

    ClearResultsPermanent wsRes

    Dim lastArm As Long, lastSel As Long
    lastArm = wsArm.Cells(wsArm.Rows.count, 2).End(xlUp).Row
    lastSel = wsSel.Cells(wsSel.Rows.count, 2).End(xlUp).Row

    If lastArm < 6 And lastSel < 6 Then
        MsgBox "Nenhum dado carregado em ARMPIL ou SELE.", vbExclamation
        GoTo Cleanup
    End If

    If lastArm < 6 Then
        MsgBox "Nenhum dado carregado em ARMPIL.", vbExclamation
        GoTo Cleanup
    End If

    If lastSel < 6 Then
        MsgBox "Nenhum dado carregado em SELE.", vbExclamation
        GoTo Cleanup
    End If

    Dim dict As Object
    Set dict = CreateObject("Scripting.Dictionary")

    If lastArm >= 6 Then
        AddKeysFromData dict, wsArm.Range("B6:C" & lastArm).Value2
    End If
    If lastSel >= 6 Then
        AddKeysFromData dict, wsSel.Range("B6:C" & lastSel).Value2
    End If

    If dict.count = 0 Then
        MsgBox "Nenhuma chave válida encontrada para comparar.", vbExclamation
        GoTo Cleanup
    End If

    Dim resCount As Long
    resCount = dict.count

    Dim dataOut() As Variant
    ReDim dataOut(1 To resCount, 1 To 2)

    Dim i As Long
    Dim k As Variant
    i = 0
    For Each k In dict.keys
        i = i + 1
        dataOut(i, 1) = dict(k)(0)
        dataOut(i, 2) = dict(k)(1)
    Next k

    Dim firstResRow As Long
    Dim lastResRow As Long
    firstResRow = 9
    lastResRow = firstResRow + resCount - 1

    With wsRes
        .Range(.Cells(firstResRow, 2), .Cells(lastResRow, 3)).Value2 = dataOut
        .Range(.Cells(firstResRow, 4), .Cells(lastResRow, 4)).FormulaR1C1 = "=UPPER(TRIM(RC[-2]))&""|""&RC[-1]"

        If lastArm >= 6 Then
            .Range(.Cells(firstResRow, 5), .Cells(lastResRow, 5)).FormulaR1C1 = _
                "=IFERROR(INDEX(ARMPIL!R6C4:R" & lastArm & "C4,MATCH(RC4,ARMPIL!R6C7:R" & lastArm & "C7,0)),"""")"
            .Range(.Cells(firstResRow, 6), .Cells(lastResRow, 6)).FormulaR1C1 = _
                "=IFERROR(INDEX(ARMPIL!R6C5:R" & lastArm & "C5,MATCH(RC4,ARMPIL!R6C7:R" & lastArm & "C7,0)),"""")"
            .Range(.Cells(firstResRow, 7), .Cells(lastResRow, 7)).FormulaR1C1 = _
                "=IFERROR(INDEX(ARMPIL!R6C6:R" & lastArm & "C6,MATCH(RC4,ARMPIL!R6C7:R" & lastArm & "C7,0)),"""")"
        End If

        If lastSel >= 6 Then
            .Range(.Cells(firstResRow, 8), .Cells(lastResRow, 8)).FormulaR1C1 = _
                "=IFERROR(INDEX(SELE!R6C4:R" & lastSel & "C4,MATCH(RC4,SELE!R6C5:R" & lastSel & "C5,0)),"""")"
        End If

        .Range(.Cells(firstResRow, 9), .Cells(lastResRow, 9)).FormulaR1C1 = _
            "=IF(OR(RC[-2]="""",RC[-1]=""""),"""",IF(AND(ISNUMBER(RC[-2]),ISNUMBER(RC[-1])),RC[-2]-RC[-1],""""))"
        .Range(.Cells(firstResRow, 10), .Cells(lastResRow, 10)).FormulaR1C1 = _
            "=IF(OR(RC[-3]="""",RC[-2]=""""),""SEM MATCH"",IF(NOT(ISNUMBER(RC[-2])),""NAO DIMENSIONADO"",IF(RC[-3]>=RC[-2],""APROVADO"",IF(RC[-3]*1.15>=RC[-2],""MARGEM 15%"",""REPROVADO""))))"
        .Range(.Cells(firstResRow, 4), .Cells(lastResRow, 10)).Calculate
    End With

    SortSheetRangeByPilarLance wsRes, firstResRow, lastResRow, 2, 10, 2, 3, 11
    wsRes.Range(wsRes.Cells(firstResRow, 4), wsRes.Cells(lastResRow, 10)).Calculate

    FormatResultadoRange wsRes, firstResRow, lastResRow
    AtualizarResumoResultado wsRes, lastResRow
    ConfigurarFormatacaoCondicionalResultado wsRes, lastResRow
    InicializarFiltrosResultado False
    ReaplicarFiltrosResultado
    CompareAndMark = True

    If showSuccessMessage Then
        wsRes.Activate
        MsgBox "Resultado preparado com formulas permanentes.", vbInformation
    End If

Cleanup:
    RestoreExcelBatch state
    If Err.Number <> 0 Then
        MsgBox "Erro na comparacao: " & Err.Description, vbExclamation
    End If
End Function

Public Sub AddKeysFromData(ByRef dict As Object, ByVal data As Variant)
    Dim i As Long
    Dim pilar As String
    Dim lanceTxt As String
    Dim chave As String

    If Not IsArray(data) Then Exit Sub

    For i = 1 To UBound(data, 1)
        pilar = NormalizePilarName(CStr(data(i, 1)))
        lanceTxt = Trim$(CStr(data(i, 2)))
        If pilar <> "" And lanceTxt <> "" Then
            chave = BuildPilarKey(pilar, lanceTxt)
            If Not dict.Exists(chave) Then dict.Add chave, Array(pilar, data(i, 2))
        End If
    Next i
End Sub

Public Sub ClearResultsPermanent(ByVal ws As Worksheet)
    Dim lr As Long
    lr = ws.Cells(ws.Rows.count, 2).End(xlUp).Row

    PrepararCabecalhoResultado ws
    FormatResultadoHeaderRow ws

    If lr >= 9 Then
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 13)).ClearContents
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).Interior.Color = RGB(247, 248, 252)
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).Font.Color = RGB(44, 62, 80)
        ws.Range(ws.Cells(9, 2), ws.Cells(lr, 10)).Borders.LineStyle = xlNone
    End If

    ws.Range(ws.Cells(6, 2), ws.Cells(6, 7)).Value = "--"
    InicializarFiltrosResultado False
    ReaplicarFiltrosResultado
End Sub

Public Sub PrepararCabecalhoResultado(ByVal ws As Worksheet)
    With ws.Range("B1:J2")
        .UnMerge
        .ClearContents
        .Interior.Pattern = xlNone
        .Borders.LineStyle = xlNone
        .Font.Name = "Segoe UI"
        .Font.Color = RGB(30, 30, 28)
    End With

    With ws.Range("B1:J1")
        .Merge
        .Value = "AUDITORIA DE ARMADURA - ARMPIL x SELE"
        .Interior.Color = RGB(30, 30, 28)
        .Font.Color = RGB(255, 255, 255)
        .Font.Bold = True
        .Font.Size = 13
        .HorizontalAlignment = xlLeft
        .VerticalAlignment = xlCenter
    End With

    With ws.Range("B2:J2")
        .Merge
        .Value = "Compara As projetada no ARMPIL com As minima do SELE. Vermelho = nao atende o minimo."
        .Font.Italic = True
        .Font.Size = 9
        .Font.Color = RGB(90, 90, 90)
        .HorizontalAlignment = xlLeft
        .VerticalAlignment = xlCenter
    End With

    ws.Range("B5:G5").Value = Array("PILARES", "LANCES", "APROVADOS", "MARGEM 15%", "REPROVADOS", "SEM MATCH")

    With ws.Range("B5:G5")
        .Interior.Color = RGB(234, 243, 222)
        .Font.Bold = True
        .Font.Size = 9
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .Borders.LineStyle = xlContinuous
        .Borders.Color = RGB(180, 178, 169)
    End With

    With ws.Range("B6:G6")
        .Interior.Color = RGB(248, 247, 244)
        .Font.Bold = True
        .Font.Size = 11
        .Font.Color = RGB(59, 109, 17)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .Borders.LineStyle = xlContinuous
        .Borders.Color = RGB(180, 178, 169)
    End With

    ws.Rows("1:2").RowHeight = 20
    ws.Rows("5:7").RowHeight = 20
    ws.Rows(1).RowHeight = 28
End Sub

Public Sub FormatResultadoRange(ByVal ws As Worksheet, ByVal rowStart As Long, ByVal rowEnd As Long)
    If rowEnd < rowStart Then Exit Sub

    Dim rg As Range
    Set rg = ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 10))

    FormatResultadoHeaderRow ws

    With rg
        .Font.Name = "Segoe UI"
        .Font.Size = 9
        .Font.Color = RGB(44, 62, 80)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .Borders.LineStyle = xlNone
        .Borders(xlInsideHorizontal).LineStyle = xlContinuous
        .Borders(xlInsideHorizontal).Color = RGB(222, 226, 232)
        .Borders(xlEdgeBottom).LineStyle = xlContinuous
        .Borders(xlEdgeBottom).Color = RGB(189, 195, 208)
    End With

    ws.Range(ws.Cells(rowStart, 5), ws.Cells(rowEnd, 8)).NumberFormat = "0.00"
    ws.Range(ws.Cells(rowStart, 9), ws.Cells(rowEnd, 9)).NumberFormat = "+0.00;-0.00;0.00"
    ws.Range(ws.Cells(rowStart, 2), ws.Cells(rowEnd, 2)).Font.Bold = True
    ws.Range(ws.Cells(rowStart, 10), ws.Cells(rowEnd, 10)).Font.Bold = True
    ws.Rows(rowStart & ":" & rowEnd).RowHeight = 20

    ApplyResultadoKeyColumnEmphasis ws, rowStart, rowEnd
    ApplyResultadoPilarBlockSeparators ws, rowStart, rowEnd, 2, 2, 10
End Sub

Public Sub AtualizarResumoResultado(ByVal ws As Worksheet, ByVal lastRow As Long)
    If lastRow < 9 Then Exit Sub

    ws.Cells(6, 2).FormulaLocal = "=SOMARPRODUTO((B9:B" & lastRow & "<>"""")/CONT.SE(B9:B" & lastRow & ";B9:B" & lastRow & "&""""))"
    ws.Cells(6, 3).FormulaLocal = "=CONT.VALORES(B9:B" & lastRow & ")"
    ws.Cells(6, 4).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""APROVADO"")"
    ws.Cells(6, 5).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""MARGEM 15%"")"
    ws.Cells(6, 6).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""REPROVADO"")"
    ws.Cells(6, 7).FormulaLocal = "=CONT.SE(J9:J" & lastRow & ";""SEM MATCH"")"
    ws.Range(ws.Cells(6, 2), ws.Cells(6, 7)).Calculate
End Sub

Public Sub ConfigurarFormatacaoCondicionalResultado(ByVal ws As Worksheet, ByVal lastRow As Long)
    If lastRow < 9 Then Exit Sub

    Dim rg As Range
    Set rg = ws.Range(ws.Cells(9, 2), ws.Cells(lastRow, 10))

    rg.FormatConditions.Delete

    ' APROVADO
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""APROVADO""")
        .Interior.Color = RGB(213, 245, 227)
        .Font.Color = RGB(30, 132, 73)
    End With

    ' MARGEM 15%
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""MARGEM 15%""")
        .Interior.Color = RGB(255, 249, 196)
        .Font.Color = RGB(133, 100, 4)
    End With

    ' REPROVADO
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""REPROVADO""")
        .Interior.Color = RGB(255, 204, 204)
        .Font.Color = RGB(192, 57, 43)
    End With

    ' SEM MATCH
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""SEM MATCH""")
        .Interior.Color = RGB(255, 249, 196)
        .Font.Color = RGB(133, 100, 4)
    End With

    ' NAO DIMENSIONADO
    With rg.FormatConditions.Add(Type:=xlExpression, Formula1:="=$J9=""NAO DIMENSIONADO""")
        .Interior.Color = RGB(255, 243, 224)
        .Font.Color = RGB(175, 96, 26)
    End With
End Sub
