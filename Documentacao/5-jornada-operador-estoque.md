# Jornada do Operador de Estoque

```mermaid
journey
    title Dia Típico do Operador de Estoque
    section Manhã - Recebimento
      Chegar ao trabalho: 5: Operador
      Verificar entregas do dia: 4: Operador
      Receber caminhão: 3: Operador, Fornecedor
      Conferir material: 3: Operador
      Pesar material: 4: Operador
      Registrar no sistema: 5: Operador, Sistema
      Imprimir etiquetas: 5: Operador, Sistema
      Organizar no estoque: 4: Operador
    section Tarde - Atendimento
      Receber requisição: 4: Operador, Produção
      Localizar material: 5: Operador, Sistema
      Escanear código: 5: Operador, Sistema
      Registrar saída: 5: Operador, Sistema
      Entregar material: 5: Operador, Produção
      Atualizar localização: 4: Operador, Sistema
    section Final do Dia
      Verificar pendências: 4: Operador
      Gerar relatório diário: 5: Operador, Sistema
      Organizar área: 5: Operador
```