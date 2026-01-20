/**
 * Designer Visual de Etiquetas EPL
 * Sistema drag-and-drop para criação de templates de etiquetas
 */

class LabelDesigner {
    constructor(canvasId, initialTemplate = null) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.scale = 3; // 3 pixels por milímetro para visualização

        this.elements = [];
        this.selectedElement = null;
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };

        // Dimensões da etiqueta em mm (obtidas dos inputs)
        this.labelWidth = parseFloat(document.getElementById('labelWidth').value) || 100;
        this.labelHeight = parseFloat(document.getElementById('labelHeight').value) || 50;

        // Carregar template inicial se fornecido
        if (initialTemplate && initialTemplate.elements) {
            this.elements = initialTemplate.elements;
        }

        this.setupEventListeners();
        this.updateCanvasSize();
        this.render();
    }

    setupEventListeners() {
        // Canvas events
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));

        // Keyboard events
        document.addEventListener('keydown', this.onKeyDown.bind(this));

        // Button events
        document.getElementById('addTextBtn').addEventListener('click', () => this.addElement('text'));
        document.getElementById('addBarcodeBtn').addEventListener('click', () => this.addElement('barcode'));
        document.getElementById('deleteElementBtn').addEventListener('click', () => this.deleteSelectedElement());
        document.getElementById('saveTemplateBtn').addEventListener('click', () => this.saveTemplate());

        // Label dimension changes
        document.getElementById('labelWidth').addEventListener('change', () => this.updateCanvasSize());
        document.getElementById('labelHeight').addEventListener('change', () => this.updateCanvasSize());
    }

    updateCanvasSize() {
        this.labelWidth = parseFloat(document.getElementById('labelWidth').value) || 100;
        this.labelHeight = parseFloat(document.getElementById('labelHeight').value) || 50;

        this.canvas.width = this.labelWidth * this.scale;
        this.canvas.height = this.labelHeight * this.scale;

        this.render();
    }

    addElement(type) {
        const element = {
            type: type,
            field: type === 'text' ? 'code' : 'code',
            x: 10,
            y: 10,
            width: type === 'barcode' ? 80 : 40,
            height: type === 'barcode' ? 15 : 8,
            rotation: 0
        };

        if (type === 'text') {
            element.font_size = 2;
            element.font_multiplier_h = 1;
            element.font_multiplier_v = 1;
            element.label = '';
        } else if (type === 'barcode') {
            element.barcode_type = '128';
            element.human_readable = true;
        }

        this.elements.push(element);
        this.selectedElement = element;
        this.render();
        this.showElementProperties();
    }

    deleteSelectedElement() {
        if (this.selectedElement) {
            const index = this.elements.indexOf(this.selectedElement);
            if (index > -1) {
                this.elements.splice(index, 1);
                this.selectedElement = null;
                this.render();
                this.hideElementProperties();
            }
        }
    }

    onMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) / this.scale;
        const y = (e.clientY - rect.top) / this.scale;

        // Verificar se clicou em algum elemento
        for (let i = this.elements.length - 1; i >= 0; i--) {
            const elem = this.elements[i];
            if (x >= elem.x && x <= elem.x + elem.width &&
                y >= elem.y && y <= elem.y + elem.height) {
                this.selectedElement = elem;
                this.isDragging = true;
                this.dragOffset = {
                    x: x - elem.x,
                    y: y - elem.y
                };
                this.render();
                this.showElementProperties();
                return;
            }
        }

        // Clicou no canvas vazio
        this.selectedElement = null;
        this.render();
        this.hideElementProperties();
    }

    onMouseMove(e) {
        if (this.isDragging && this.selectedElement) {
            const rect = this.canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) / this.scale;
            const y = (e.clientY - rect.top) / this.scale;

            this.selectedElement.x = Math.max(0, Math.min(x - this.dragOffset.x, this.labelWidth - this.selectedElement.width));
            this.selectedElement.y = Math.max(0, Math.min(y - this.dragOffset.y, this.labelHeight - this.selectedElement.height));

            this.render();
            this.updatePropertyInputs();
        }
    }

    onMouseUp(e) {
        this.isDragging = false;
    }

    onKeyDown(e) {
        if (e.key === 'Delete' && this.selectedElement) {
            this.deleteSelectedElement();
        }
    }

    render() {
        // Limpar canvas
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Desenhar grid de referência (a cada 10mm)
        this.ctx.strokeStyle = '#e0e0e0';
        this.ctx.lineWidth = 1;
        for (let i = 10; i < this.labelWidth; i += 10) {
            this.ctx.beginPath();
            this.ctx.moveTo(i * this.scale, 0);
            this.ctx.lineTo(i * this.scale, this.canvas.height);
            this.ctx.stroke();
        }
        for (let i = 10; i < this.labelHeight; i += 10) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, i * this.scale);
            this.ctx.lineTo(this.canvas.width, i * this.scale);
            this.ctx.stroke();
        }

        // Desenhar borda da etiqueta
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(0, 0, this.canvas.width, this.canvas.height);

        // Desenhar elementos
        this.elements.forEach(elem => {
            this.renderElement(elem);
        });

        // Atualizar botão de deletar
        document.getElementById('deleteElementBtn').disabled = !this.selectedElement;
    }

    renderElement(elem) {
        const x = elem.x * this.scale;
        const y = elem.y * this.scale;
        const width = elem.width * this.scale;
        const height = elem.height * this.scale;

        // Destacar elemento selecionado
        if (elem === this.selectedElement) {
            this.ctx.fillStyle = 'rgba(0, 123, 255, 0.1)';
            this.ctx.fillRect(x, y, width, height);
            this.ctx.strokeStyle = '#007bff';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(x, y, width, height);
        } else {
            this.ctx.strokeStyle = '#999';
            this.ctx.lineWidth = 1;
            this.ctx.strokeRect(x, y, width, height);
        }

        // Renderizar conteúdo baseado no tipo
        if (elem.type === 'text') {
            this.renderTextElement(elem, x, y, width, height);
        } else if (elem.type === 'barcode') {
            this.renderBarcodeElement(elem, x, y, width, height);
        }
    }

    renderTextElement(elem, x, y, width, height) {
        const label = elem.label || '';
        const field = this.getFieldDisplayName(elem.field);
        const text = label ? `${label} ${field}` : field;

        this.ctx.fillStyle = '#000';
        this.ctx.font = `${12 * (elem.font_multiplier_v || 1)}px monospace`;
        this.ctx.fillText(text, x + 5, y + height / 2 + 5);

        // Mostrar ícone de texto
        this.ctx.font = '10px Arial';
        this.ctx.fillStyle = '#666';
        this.ctx.fillText('A', x + 2, y + 10);
    }

    renderBarcodeElement(elem, x, y, width, height) {
        // Simular código de barras com barras verticais
        this.ctx.fillStyle = '#000';
        const barWidth = 2;
        const gap = 1;
        for (let i = x; i < x + width; i += (barWidth + gap)) {
            const barHeight = (i % 3 === 0) ? height - 15 : height - 10;
            this.ctx.fillRect(i, y, barWidth, barHeight);
        }

        // Texto legível (se habilitado)
        if (elem.human_readable) {
            const field = this.getFieldDisplayName(elem.field);
            this.ctx.font = '10px monospace';
            this.ctx.fillStyle = '#000';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(field, x + width / 2, y + height - 2);
            this.ctx.textAlign = 'left';
        }

        // Mostrar ícone de código de barras
        this.ctx.font = '10px Arial';
        this.ctx.fillStyle = '#666';
        this.ctx.fillText('|||', x + 2, y + 10);
    }

    getFieldDisplayName(field) {
        const names = {
            'code': '[Código]',
            'location_code': '[Local]',
            'warehouse': '[Armazém]',
            'capacity': '[Capacidade]',
            'status': '[Status]'
        };
        return names[field] || '[Campo]';
    }

    showElementProperties() {
        if (!this.selectedElement) return;

        const panel = document.getElementById('elementPropertiesPanel');
        const container = document.getElementById('elementProperties');
        panel.style.display = 'block';

        const elem = this.selectedElement;
        let html = `
            <div class="form-group">
                <label>Tipo</label>
                <input type="text" class="form-control" value="${elem.type === 'text' ? 'Texto' : 'Código de Barras'}" readonly>
            </div>
            <div class="form-group">
                <label>Campo do Bin</label>
                <select class="form-control" id="propField">
                    <option value="code" ${elem.field === 'code' ? 'selected' : ''}>Código do Bin</option>
                    <option value="location_code" ${elem.field === 'location_code' ? 'selected' : ''}>Código de Localização</option>
                    <option value="warehouse" ${elem.field === 'warehouse' ? 'selected' : ''}>Armazém</option>
                    <option value="capacity" ${elem.field === 'capacity' ? 'selected' : ''}>Capacidade</option>
                    <option value="status" ${elem.field === 'status' ? 'selected' : ''}>Status</option>
                </select>
            </div>
            <div class="row">
                <div class="col-6">
                    <div class="form-group">
                        <label>X (mm)</label>
                        <input type="number" class="form-control" id="propX" value="${elem.x.toFixed(1)}" step="0.1">
                    </div>
                </div>
                <div class="col-6">
                    <div class="form-group">
                        <label>Y (mm)</label>
                        <input type="number" class="form-control" id="propY" value="${elem.y.toFixed(1)}" step="0.1">
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-6">
                    <div class="form-group">
                        <label>Largura (mm)</label>
                        <input type="number" class="form-control" id="propWidth" value="${elem.width}" step="1">
                    </div>
                </div>
                <div class="col-6">
                    <div class="form-group">
                        <label>Altura (mm)</label>
                        <input type="number" class="form-control" id="propHeight" value="${elem.height}" step="1">
                    </div>
                </div>
            </div>
        `;

        if (elem.type === 'text') {
            html += `
                <div class="form-group">
                    <label>Label (opcional)</label>
                    <input type="text" class="form-control" id="propLabel" value="${elem.label || ''}" placeholder="Ex: Código:">
                </div>
                <div class="form-group">
                    <label>Tamanho da Fonte</label>
                    <select class="form-control" id="propFontSize">
                        <option value="1" ${elem.font_size === 1 ? 'selected' : ''}>1 (Pequeno)</option>
                        <option value="2" ${elem.font_size === 2 ? 'selected' : ''}>2 (Médio)</option>
                        <option value="3" ${elem.font_size === 3 ? 'selected' : ''}>3 (Grande)</option>
                        <option value="4" ${elem.font_size === 4 ? 'selected' : ''}>4 (Extra Grande)</option>
                        <option value="5" ${elem.font_size === 5 ? 'selected' : ''}>5 (Enorme)</option>
                    </select>
                </div>
                <div class="row">
                    <div class="col-6">
                        <div class="form-group">
                            <label>Mult. Horizontal</label>
                            <input type="number" class="form-control" id="propMultH" value="${elem.font_multiplier_h}" min="1" max="8">
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="form-group">
                            <label>Mult. Vertical</label>
                            <input type="number" class="form-control" id="propMultV" value="${elem.font_multiplier_v}" min="1" max="8">
                        </div>
                    </div>
                </div>
            `;
        } else if (elem.type === 'barcode') {
            html += `
                <div class="form-group">
                    <label>Tipo de Código</label>
                    <select class="form-control" id="propBarcodeType">
                        <option value="128" ${elem.barcode_type === '128' ? 'selected' : ''}>Code 128</option>
                        <option value="39" ${elem.barcode_type === '39' ? 'selected' : ''}>Code 39</option>
                    </select>
                </div>
                <div class="form-check">
                    <input type="checkbox" class="form-check-input" id="propHumanReadable" ${elem.human_readable ? 'checked' : ''}>
                    <label class="form-check-label" for="propHumanReadable">
                        Mostrar texto legível
                    </label>
                </div>
            `;
        }

        container.innerHTML = html;

        // Adicionar event listeners
        this.attachPropertyListeners();
    }

    attachPropertyListeners() {
        const inputs = ['propField', 'propX', 'propY', 'propWidth', 'propHeight', 'propLabel',
                       'propFontSize', 'propMultH', 'propMultV', 'propBarcodeType', 'propHumanReadable'];

        inputs.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.addEventListener('change', () => this.updateElementFromProperties());
                elem.addEventListener('input', () => this.updateElementFromProperties());
            }
        });
    }

    updateElementFromProperties() {
        if (!this.selectedElement) return;

        const elem = this.selectedElement;

        // Propriedades comuns
        elem.field = document.getElementById('propField')?.value || elem.field;
        elem.x = parseFloat(document.getElementById('propX')?.value) || elem.x;
        elem.y = parseFloat(document.getElementById('propY')?.value) || elem.y;
        elem.width = parseFloat(document.getElementById('propWidth')?.value) || elem.width;
        elem.height = parseFloat(document.getElementById('propHeight')?.value) || elem.height;

        // Propriedades específicas de texto
        if (elem.type === 'text') {
            elem.label = document.getElementById('propLabel')?.value || '';
            elem.font_size = parseInt(document.getElementById('propFontSize')?.value) || 2;
            elem.font_multiplier_h = parseInt(document.getElementById('propMultH')?.value) || 1;
            elem.font_multiplier_v = parseInt(document.getElementById('propMultV')?.value) || 1;
        }

        // Propriedades específicas de código de barras
        if (elem.type === 'barcode') {
            elem.barcode_type = document.getElementById('propBarcodeType')?.value || '128';
            elem.human_readable = document.getElementById('propHumanReadable')?.checked || false;
        }

        this.render();
    }

    updatePropertyInputs() {
        if (!this.selectedElement) return;

        const elem = this.selectedElement;
        document.getElementById('propX').value = elem.x.toFixed(1);
        document.getElementById('propY').value = elem.y.toFixed(1);
    }

    hideElementProperties() {
        document.getElementById('elementPropertiesPanel').style.display = 'none';
    }

    async saveTemplate() {
        const name = document.getElementById('templateName').value.trim();
        const description = document.getElementById('templateDescription').value.trim();
        const width = parseFloat(document.getElementById('labelWidth').value);
        const height = parseFloat(document.getElementById('labelHeight').value);
        const dpi = parseInt(document.getElementById('printerDPI').value);
        const isDefault = document.getElementById('isDefault').checked;
        const templateId = document.getElementById('templateId').value;

        // Validação
        if (!name) {
            alert('Por favor, informe um nome para o template.');
            return;
        }

        if (!width || !height) {
            alert('Por favor, informe a largura e altura da etiqueta.');
            return;
        }

        // Preparar dados
        const data = {
            template_id: templateId || null,
            name: name,
            description: description,
            width_mm: width,
            height_mm: height,
            printer_dpi: dpi,
            is_default: isDefault,
            template_json: {
                elements: this.elements
            }
        };

        try {
            const response = await fetch('/labels/templates/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                alert('Template salvo com sucesso!');
                window.location.href = '/labels/templates/';
            } else {
                alert('Erro ao salvar template: ' + result.error);
            }
        } catch (error) {
            alert('Erro ao salvar template: ' + error.message);
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}
