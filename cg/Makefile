all: modes/spa-eng.mode ita-eng modes.xml
	sacrebleu -i ita-eng.out.txt eng.ref.txt

CORPUS="train"
#CORPUS="dev"
#CORPUS="test"

modes/spa-eng.mode: modes.xml
	apertium-gen-modes $<

spa-eng: eng.ref.txt spa-eng.out.txt
fra-eng: eng.ref.txt fra-eng.out.txt
ita-eng: eng.ref.txt ita-eng.out.txt

eng.ref.txt: UD_English-PUD/en_pud-ud-test.conllu
	./select.py $(CORPUS) text $< > $@

spa-eng.out.txt: UD_Spanish-PUD/es_pud-ud-test.conllu spa.udx text.sh spa-eng.cg.bin eng.cg.bin
	./select.py $(CORPUS) tree $< | ./text.sh spa eng > $@

fra-eng.out.txt: UD_French-PUD/fr_pud-ud-test.conllu fra.udx text.sh fra-eng.cg.bin eng.cg.bin fra-eng.autobil.bin
	$(MAKE) -C apertium-fra-eng
	./select.py $(CORPUS) tree $< | ./text.sh fra eng_clean > $@

ita-eng.out.txt: UD_Italian-PUD/it_pud-ud-test.conllu ita.udx text.sh ita-eng.cg.bin eng.cg.bin ita-eng.autobil.bin
	$(MAKE) -C apertium-eng-ita
	./select.py $(CORPUS) tree $< | ./text.sh ita eng_clean > $@

%.cg.bin: %.cg
	cg-comp $< $@

fra-eng.tagrelax.hfst: fra-eng.tagrelax.xfst
	hfst-regexp2fst -S $< -o $@

ita-eng.tagrelax.hfst: ita-eng.tagrelax.xfst
	hfst-regexp2fst -S $< -o $@

fra-eng.autobil.att: apertium-fra-eng/fra-eng.autobil.bin fra-eng.tagrelax.hfst
	$(MAKE) -C apertium-fra-eng
	lt-print -H $< | hfst-txt2fst | hfst-invert | \
		hfst-compose -1 - -2 fra-eng.tagrelax.hfst | hfst-invert | \
		hfst-fst2txt -o $@

ita-eng.autobil.att: apertium-eng-ita/ita-eng.autobil.bin ita-eng.tagrelax.hfst
	$(MAKE) -C apertium-eng-ita
	lt-print -H $< | hfst-txt2fst | hfst-invert | \
		hfst-compose -1 - -2 ita-eng.tagrelax.hfst | hfst-invert | \
		hfst-fst2txt -o $@

%.autobil.bin: %.autobil.att
	lt-comp -S lr $< $@

clean:
	rm -rf *.txt *.bin modes
