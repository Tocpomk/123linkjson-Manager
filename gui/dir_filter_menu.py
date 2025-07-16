import re

class DirFilterMenu:
    """
    目录筛选与多级下拉菜单生成工具
    """
    def __init__(self, files):
        self.files = files or []
        self.dir_tree = self._build_dir_tree()

    def _build_dir_tree(self):
        """
        构建二级、三级目录树结构
        返回：{二级目录: set(三级目录)}
        """
        tree = {}
        for f in self.files:
            path = f.get('path', '')
            parts = path.split('/')
            if len(parts) > 1:
                second = parts[0]
                third = parts[1] if len(parts) > 2 else None
                if second not in tree:
                    tree[second] = set()
                if third:
                    tree[second].add(third)
        return tree

    def get_menu_options(self):
        """
        获取下拉菜单选项：
        - 只有全部
        - 有二级目录时，全部+二级目录（超7字省略...）
        - 二级目录过多时，支持展开三级目录
        返回：
        [
            {'label': '全部', 'value': '全部'},
            {'label': '二级目录名', 'value': '二级目录', 'children': [ {'label': '三级目录', 'value': '二级/三级'} ]},
            ...
        ]
        """
        tree = self.dir_tree
        if not tree:
            return [{'label': '全部', 'value': '全部'}]
        options = [{'label': '全部', 'value': '全部'}]
        for second, thirds in tree.items():
            label = self._shorten(second)
            if thirds:
                children = [
                    {'label': self._shorten(t), 'value': f'{second}/{t}'} for t in sorted(thirds)
                ]
                options.append({'label': label, 'value': second, 'children': children})
            else:
                options.append({'label': label, 'value': second})
        return options

    def _shorten(self, name):
        if len(name) > 7:
            return name[:7] + '...'
        return name

    def filter_files(self, select_value):
        """
        根据下拉选项过滤文件
        select_value: '全部' | '二级目录' | '二级/三级'
        """
        if select_value == '全部':
            return self.files
        elif '/' in select_value:
            # 二级/三级
            second, third = select_value.split('/', 1)
            return [f for f in self.files if f.get('path', '').startswith(f'{second}/{third}/') or f.get('path', '') == f'{second}/{third}']
        else:
            # 二级目录
            return [f for f in self.files if f.get('path', '').startswith(f'{select_value}/')] 