# Troubleshooting: Impressora Não Imprime (TCP OK, Status SUCCESS)

## Situação Atual

- ✅ Conexão TCP funciona (10.1.82.23:9100)
- ✅ PrintJob marcado como SUCCESS
- ✅ Comandos EPL enviados
- ❌ **Nenhuma etiqueta física impressa**

## Possíveis Causas e Soluções

### 1. Impressora em Modo Standby/Sleep

**Sintoma**: Conexão funciona mas não imprime
**Causa**: Impressora aceita dados mas não processa

**Solução**:
- Pressione o botão de alimentação da impressora
- Verifique se o LED está verde (não laranja/piscando)
- Imprima uma página de teste diretamente na impressora

### 2. Falta de Papel/Etiquetas

**Sintoma**: Conexão OK, mas nada sai

**Solução**:
- Verifique se há etiquetas carregadas
- Verifique sensor de papel
- Imprima auto-teste: segurar botão FEED ao ligar

### 3. Impressora é ZPL, não EPL

**Sintoma**: Aceita comandos mas não processa EPL

**Modelos que usam ZPL**:
- Zebra GK/GX/ZT/ZD series
- Zebra S4M, ZM series
- Zebra 105SL, 110XiIII

**Solução**: Verificar manual ou tentar comandos ZPL

**Teste ZPL**:
```zpl
^XA
^FO50,50^A0N,50,50^FDTeste^FS
^XZ
```

### 4. Configuração de Tamanho de Etiqueta

**Sintoma**: Impressora pula etiquetas ou imprime em branco

**Causa**: Tamanho configurado na impressora diferente do EPL

**Nosso EPL**: Q799,0 = ~100mm largura (203 DPI)

**Solução**:
1. Verificar tamanho real da etiqueta física
2. Calibrar impressora:
   - Segurar FEED ao ligar
   - Aguardar calibração automática
3. Ajustar template para tamanho correto

### 5. DPI Incorreto

**Sintoma**: Etiqueta sai distorcida ou não imprime

**Template atual**: 203 DPI
**Impressora pode ser**: 300 DPI ou 203 DPI

**Solução**:
- Verificar DPI real da impressora (manual ou auto-teste)
- Ajustar template no admin (/admin/labels/labeltemplate/)
- Recriar template com DPI correto

### 6. Modo de Impressão (Térmico Direto vs Transferência Térmica)

**Sintoma**: Etiqueta sai em branco

**Causa**: Falta ribbon (se transferência térmica)

**Solução**:
- Verificar se impressora usa ribbon
- Instalar ribbon se necessário
- OU configurar para modo térmico direto

### 7. Buffer Cheio ou Travado

**Sintoma**: Primeira impressão funciona, depois para

**Solução**:
```python
# Reset da impressora via comando EPL
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('10.1.82.23', 9100))
sock.sendall(b'\x1b@\r\n')  # Reset
sock.close()
```

### 8. Firmware Antigo ou Incompatível

**Sintoma**: Comandos EPL não reconhecidos

**Solução**:
- Atualizar firmware da impressora
- Verificar compatibilidade EPL no manual
- Testar com comandos EPL básicos

### 9. Configuração de Rede/Protocolo

**Sintoma**: Conexão TCP OK mas dados não processam

**Solução**:
- Verificar se impressora está em modo RAW (não IPP/LPD)
- Porta 9100 deve ser RAW printing
- Desabilitar "wait for job" nas configurações da impressora

### 10. Densidade/Temperatura Muito Baixa

**Sintoma**: Etiqueta sai muito clara ou invisível

**Solução**:
- Aumentar densidade no comando EPL (D10 → D15)
- Ajustar controle de temperatura na impressora
- Verificar cabeça de impressão

## Diagnóstico Passo a Passo

### Passo 1: Verificar Físico

```bash
# Execute o diagnóstico
venv/bin/python diagnose_printer.py
```

**Perguntas**:
- [ ] Etiqueta saiu? (mesmo em branco ou com erro?)
- [ ] LED da impressora está verde?
- [ ] Há papel/etiquetas carregadas?
- [ ] Impressora faz barulho ao receber dados?

### Passo 2: Auto-Teste da Impressora

**Como fazer** (varia por modelo):
1. Desligue a impressora
2. Segure botão FEED
3. Ligue a impressora (ainda segurando FEED)
4. Solte após 3 segundos
5. Deve imprimir página de configuração

**O que verificar**:
- Modelo da impressora
- Firmware version
- Linguagem (EPL ou ZPL?)
- DPI (203 ou 300?)
- Tamanho de etiqueta configurado

### Passo 3: Testar Comandos Manualmente

**Usar Netcat** (Linux/Mac):
```bash
# Teste EPL
echo -e "N\nQ203,16\nq203\nA10,10,0,3,1,1,N,\"TESTE\"\nP1" | nc 10.1.82.23 9100

# Teste ZPL (se EPL não funcionar)
echo -e "^XA\n^FO50,50^A0N,50,50^FDTeste^FS\n^XZ" | nc 10.1.82.23 9100
```

**Windows** (PowerShell):
```powershell
$socket = New-Object System.Net.Sockets.TcpClient('10.1.82.23', 9100)
$stream = $socket.GetStream()
$writer = New-Object System.IO.StreamWriter($stream)
$writer.WriteLine("N")
$writer.WriteLine("Q203,16")
$writer.WriteLine("q203")
$writer.WriteLine('A10,10,0,3,1,1,N,"TESTE"')
$writer.WriteLine("P1")
$writer.Flush()
$stream.Close()
$socket.Close()
```

### Passo 4: Verificar Logs da Impressora

**Se impressora tem interface web**:
1. Acesse http://10.1.82.23 no navegador
2. Veja logs/status
3. Verifique trabalhos em fila

### Passo 5: Testar com Software do Fabricante

**Download**:
- Zebra: Zebra Setup Utilities
- Eltron: Eltron Configuration Utility
- Datamax: DataMax Print Utility

**Teste**:
1. Instale software oficial
2. Configure impressora
3. Imprima etiqueta de teste
4. Se funcionar, compare comandos gerados

## Soluções Rápidas

### Solução 1: Aumentar Densidade

Editar `apps/labels/epl_generator.py`:
```python
# Linha 44, trocar D10 por D15
commands.append("D15")  # Densidade máxima
```

### Solução 2: Adicionar Delay

Editar `apps/labels/printer_client.py`:
```python
# Após sock.sendall(encoded_data), adicionar:
import time
time.sleep(0.5)  # Aguardar 500ms
```

### Solução 3: Forçar EPL Line Mode

No início do EPL, adicionar:
```python
commands.insert(0, "I8,A,001")  # Code page 850
commands.insert(1, "OD")        # Disable auto-detect
```

### Solução 4: Tentar ZPL em Vez de EPL

Criar novo gerador ZPL se impressora for Zebra moderna:
```python
def generate_zpl(bin_obj):
    zpl = f"""^XA
^FO50,50^A0N,50,50^FD{bin_obj.code}^FS
^FO50,150^BAN,100,Y,N,N^FD{bin_obj.code}^FS
^XZ"""
    return zpl
```

## Scripts de Teste Criados

1. **`diagnose_printer.py`**: Diagnóstico completo
   ```bash
   venv/bin/python diagnose_printer.py
   ```

2. **`test_encoding_epl.py`**: Validar codificação
   ```bash
   venv/bin/python test_encoding_epl.py
   ```

## Checklist de Verificação

- [ ] Impressora ligada e LED verde
- [ ] Etiquetas carregadas corretamente
- [ ] Sensor de papel detectando (não em erro)
- [ ] Modo Online (não Standby)
- [ ] Auto-teste da impressora funciona
- [ ] Verificar se é EPL ou ZPL (manual/auto-teste)
- [ ] DPI do template = DPI da impressora
- [ ] Tamanho da etiqueta configurado = físico
- [ ] Ribbon instalado (se transferência térmica)
- [ ] Firmware atualizado
- [ ] Testar com software do fabricante

## Próximos Passos

1. **Execute o auto-teste** da impressora
2. **Identifique** se é EPL ou ZPL
3. **Verifique** DPI e tamanho de etiqueta
4. **Teste** com comandos manuais (netcat/powershell)
5. **Reporte** os resultados encontrados

## Informações Úteis

**Impressora atual**: Zebra/Eltron em 10.1.82.23:9100
**Template**: 100x50mm, 203 DPI
**EPL gerado**: 150 caracteres, 6 comandos

**Comandos EPL enviados**:
```epl
N
Q799,0
q799
A39,39,0,4,2,2,N,"BIN-0001"
B39,159,0,1,2,4,119,B,"BIN-0001"
A39,319,0,2,1,1,N,"Armazém: ARM-01"
A399,319,0,2,1,1,N,"Local: L1-R8-P3"
P1
```

## Recursos Externos

- [Zebra EPL Programming Guide](https://www.zebra.com/us/en/support-downloads/knowledge-articles/epl-programming-guide.html)
- [Zebra ZPL Programming Guide](https://www.zebra.com/us/en/support-downloads/knowledge-articles/zpl-programming-guide.html)
- [Online ZPL Viewer](http://labelary.com/viewer.html)

---

**Após executar os testes, reporte:**
1. Alguma etiqueta saiu após `diagnose_printer.py`?
2. O que mostrou o auto-teste da impressora?
3. Qual é o modelo exato da impressora?
4. É EPL ou ZPL?
5. Qual DPI e tamanho de etiqueta?
