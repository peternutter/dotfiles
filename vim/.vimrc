" .vimrc - Vim configuration
" Lightweight config for server/container use (use nvim for full IDE)

" ---------- Basics ----------
set nocompatible
set relativenumber
set number
set tabstop=4
set shiftwidth=4
set expandtab
set autoindent
set smartindent
set mouse=a
set encoding=utf-8
set backspace=indent,eol,start

" ---------- Search ----------
set hlsearch
set incsearch
set ignorecase
set smartcase

" ---------- Display ----------
set ruler
set showcmd
set wildmenu
set scrolloff=5
set laststatus=2
syntax on

" ---------- OSC 52 Clipboard (works over SSH/tmux) ----------
" Yank to system clipboard via OSC 52 escape sequence
" This works even on remote servers through SSH
if has('clipboard')
    set clipboard=unnamedplus
else
    " OSC 52 fallback for remote/container use
    function! Osc52Yank() abort
        let text = getreg('"')
        let encoded = substitute(system('printf "%s" ' . shellescape(text) . ' | base64 | tr -d "\n"'), '\n', '', 'g')
        let osc = "\e]52;c;" . encoded . "\x07"
        " Write directly to terminal
        if exists('$TMUX')
            " Wrap in tmux passthrough
            let osc = "\ePtmux;\e" . osc . "\e\\"
        endif
        call writefile([osc], '/dev/tty', 'b')
    endfunction

    augroup Osc52Yank
        autocmd!
        autocmd TextYankPost * if v:event.operator ==# 'y' | call Osc52Yank() | endif
    augroup END
endif

" ---------- Cursor shape ----------
" Block in normal mode, bar in insert mode
let &t_SI = "\e[6 q"
let &t_EI = "\e[2 q"
autocmd VimEnter * silent !echo -ne "\e[2 q"

" ---------- Quality of life ----------
" Don't create swap files in working directory
set directory=~/.vim/swap//
silent! call mkdir($HOME.'/.vim/swap', 'p', 0700)

" Remember cursor position
autocmd BufReadPost * if line("'\"") > 1 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
