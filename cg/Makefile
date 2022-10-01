all: modes/spa-eng.mode fra-eng modes.xml
	sacrebleu -i fra-eng.out.txt eng.ref.txt

CORPUS="train"
#CORPUS="dev"
#CORPUS="test"

modes/spa-eng.mode: modes.xml
	apertium-gen-modes $<

spa-eng: eng.ref.txt spa-eng.out.txt
fra-eng: eng.ref.txt fra-eng.out.txt

eng.ref.txt: UD_English-PUD/en_pud-ud-test.conllu
	./select.py $(CORPUS) text $< > $@

spa-eng.out.txt: UD_Spanish-PUD/es_pud-ud-test.conllu spa.udx text.sh spa-eng.cg.bin eng.cg.bin
	./select.py $(CORPUS) tree $< | ./text.sh spa eng > $@

fra-eng.out.txt: UD_French-PUD/fr_pud-ud-test.conllu fra.udx text.sh fra-eng.cg.bin eng.cg.bin fra-eng.autobil.bin
	./select.py $(CORPUS) tree $< | ./text.sh fra eng_clean > $@

%.cg.bin: %.cg
	cg-comp $< $@

fra-eng.tagrelax.hfst: fra-eng.tagrelax.xfst
	hfst-regexp2fst -S $< -o $@

fra-eng.autobil.att: apertium-fra-eng/fra-eng.autobil.bin fra-eng.tagrelax.hfst
	lt-print -H $< | hfst-txt2fst | hfst-invert | \
		hfst-compose -1 - -2 fra-eng.tagrelax.hfst | hfst-invert | \
		hfst-fst2txt -o $@

fra-eng.autobil.bin: fra-eng.autobil.att
	lt-comp -S lr $< $@

clean:
	rm -rf *.txt *.bin modes
