"""
Módulo para geração de comandos EPL (Eltron Programming Language)
"""


class EPLGenerator:
    """Gerador de comandos EPL para impressoras de etiquetas"""

    BARCODE_TYPES = {
        '128': '1',  # Code 128
        '39': '3',   # Code 39
    }

    def __init__(self, template, bin_obj):
        """
        Inicializa o gerador EPL

        Args:
            template: Instância de LabelTemplate
            bin_obj: Instância de Bin
        """
        self.template = template
        self.bin = bin_obj
        self.dpi = template.printer_dpi

    def generate(self):
        """
        Gera comandos EPL completos

        Returns:
            str: Comandos EPL
        """
        commands = []

        # Inicialização
        commands.append("N")  # Nova etiqueta
        commands.append(f"Q{self.template.width_dots},0")  # Largura da etiqueta
        commands.append(f"q{self.template.width_dots}")  # Largura do formulário

        # Processar elementos do template
        elements = self.template.template_json.get('elements', [])
        for element in elements:
            element_type = element.get('type')
            if element_type == 'text':
                commands.append(self._generate_text_command(element))
            elif element_type == 'barcode':
                commands.append(self._generate_barcode_command(element))

        # Finalização
        commands.append("P1")  # Imprimir 1 cópia

        return '\n'.join(commands)

    def _generate_text_command(self, element):
        """
        Gera comando EPL para texto

        Formato: Ah_pos,v_pos,rotation,font,h_mult,v_mult,reverse,"text"

        Args:
            element: Dicionário com configuração do elemento

        Returns:
            str: Comando EPL
        """
        # Obter dados do bin
        field_value = self._get_bin_field_value(element.get('field'))

        # Adicionar label se especificado
        label = element.get('label', '')
        if label:
            text = f"{label} {field_value}"
        else:
            text = field_value

        # Converter posição de mm para dots
        h_pos = self._mm_to_dots(element.get('x', 0))
        v_pos = self._mm_to_dots(element.get('y', 0))

        # Obter parâmetros
        rotation = element.get('rotation', 0)
        font = element.get('font_size', 2)
        h_mult = element.get('font_multiplier_h', 1)
        v_mult = element.get('font_multiplier_v', 1)
        reverse = 'N'  # Normal (não invertido)

        return f'A{h_pos},{v_pos},{rotation},{font},{h_mult},{v_mult},{reverse},"{text}"'

    def _generate_barcode_command(self, element):
        """
        Gera comando EPL para código de barras

        Formato: Bh_pos,v_pos,rotation,type,narrow,wide,height,human,"data"

        Args:
            element: Dicionário com configuração do elemento

        Returns:
            str: Comando EPL
        """
        # Obter dados do bin
        field_value = self._get_bin_field_value(element.get('field'))

        # Converter posição de mm para dots
        h_pos = self._mm_to_dots(element.get('x', 0))
        v_pos = self._mm_to_dots(element.get('y', 0))

        # Obter parâmetros
        rotation = element.get('rotation', 0)
        barcode_type = self.BARCODE_TYPES.get(element.get('barcode_type', '128'), '1')

        # Largura das barras (padrão: 2 e 4 dots)
        narrow = 2
        wide = 4

        # Altura do código de barras em dots
        height = self._mm_to_dots(element.get('height', 10))

        # Mostrar texto legível por humanos
        human = 'B' if element.get('human_readable', True) else 'N'

        return f'B{h_pos},{v_pos},{rotation},{barcode_type},{narrow},{wide},{height},{human},"{field_value}"'

    def _get_bin_field_value(self, field):
        """
        Obtém valor do campo do bin

        Args:
            field: Nome do campo

        Returns:
            str: Valor do campo
        """
        field_mapping = {
            'code': self.bin.code,
            'location_code': self.bin.location_code or '',
            'warehouse': self.bin.warehouse.code if self.bin.warehouse else '',
            'capacity': f"{self.bin.capacity} kg" if self.bin.capacity else '',
            'status': self.bin.get_status_display(),
        }

        return str(field_mapping.get(field, ''))

    def _mm_to_dots(self, mm):
        """
        Converte milímetros para dots

        Args:
            mm: Valor em milímetros

        Returns:
            int: Valor em dots
        """
        return int((mm / 25.4) * self.dpi)

    def get_bin_snapshot(self):
        """
        Cria snapshot dos dados do bin

        Returns:
            dict: Dados do bin no momento da geração
        """
        return {
            'code': self.bin.code,
            'location_code': self.bin.location_code or '',
            'warehouse_code': self.bin.warehouse.code if self.bin.warehouse else '',
            'warehouse_name': self.bin.warehouse.name if self.bin.warehouse else '',
            'capacity': str(self.bin.capacity) if self.bin.capacity else '',
            'status': self.bin.status,
            'status_display': self.bin.get_status_display(),
        }
