VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Planilha4"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Option Explicit

Private Sub Worksheet_SelectionChange(ByVal Target As Range)
    If Target Is Nothing Then Exit Sub

    On Error GoTo Fim
    Application.EnableEvents = False

    If Not Intersect(Target, Me.Range("B3:D3")) Is Nothing Then
        ToggleDropdown "Status"
        Me.Range("A1").Select
        GoTo Fim
    End If

    If Not Intersect(Target, Me.Range("E3:F3")) Is Nothing Then
        ToggleDropdown "Processamento"
        Me.Range("A1").Select
        GoTo Fim
    End If

    FecharDropdownsResultado

Fim:
    Application.EnableEvents = True
End Sub
